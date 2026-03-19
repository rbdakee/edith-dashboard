"""
Notion sync service — pulls tasks from Notion into the dashboard.
"""
import httpx

from app.config import settings
from app.domain.models import Task
from app.domain.enums import TaskStatus, Priority
from app.storage.task_repo import task_repo

# Notion → Dashboard status mapping
NOTION_TO_STATUS: dict[str, TaskStatus] = {
    "Backlog": TaskStatus.idea,
    "Todo": TaskStatus.planned,
    "In Progress": TaskStatus.in_progress,
    "Done": TaskStatus.done,
    "Cancelled": TaskStatus.archive,
}

NOTION_TO_PRIORITY: dict[str, Priority] = {
    "P0": Priority.p0,
    "P1": Priority.p1,
    "P2": Priority.p2,
    "P3": Priority.p3,
}

_HEADERS = {
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def _get_text(prop: dict) -> str:
    """Extract plain text from Notion rich_text or title property."""
    items = prop.get("rich_text") or prop.get("title") or []
    return "".join(t.get("plain_text", "") for t in items)


def _parse_notion_task(page: dict) -> dict | None:
    """Convert a Notion page to dashboard task fields."""
    props = page.get("properties", {})

    title_prop = props.get("Name") or props.get("Title") or {}
    title = _get_text(title_prop)
    if not title:
        return None

    status_name = (props.get("Status") or {}).get("select", {})
    status_name = status_name.get("name", "") if status_name else ""
    status = NOTION_TO_STATUS.get(status_name, TaskStatus.idea)

    priority_name = (props.get("Priority") or {}).get("select", {})
    priority_name = priority_name.get("name", "") if priority_name else ""
    priority = NOTION_TO_PRIORITY.get(priority_name, Priority.p2)

    category_name = (props.get("Category") or {}).get("select", {})
    category = category_name.get("name", "work").lower() if category_name else "work"

    description = _get_text(props.get("Description") or {})

    deadline_prop = (props.get("Deadline") or {}).get("date") or {}
    deadline = deadline_prop.get("start")

    return {
        "notion_id": page["id"].replace("-", ""),
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "category": category,
        "deadline": deadline,
    }


async def sync_from_notion():
    """Pull tasks from Notion into dashboard. Skips if no API key configured."""
    if not settings.notion_api_key or not settings.notion_tasks_db:
        return

    headers = {**_HEADERS, "Authorization": f"Bearer {settings.notion_api_key}"}
    url = f"https://api.notion.com/v1/databases/{settings.notion_tasks_db}/query"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json={})
        resp.raise_for_status()
        pages = resp.json().get("results", [])

    # Build index of existing tasks by notion_id
    existing = await task_repo.list()
    by_notion_id = {t.notion_id: t for t in existing if t.notion_id}

    created = 0
    updated = 0

    for page in pages:
        fields = _parse_notion_task(page)
        if not fields:
            continue

        notion_id = fields["notion_id"]

        if notion_id in by_notion_id:
            # Update existing task
            task = by_notion_id[notion_id]
            await task_repo.update(task.id, {
                "title": fields["title"],
                "description": fields["description"],
                "status": fields["status"].value if hasattr(fields["status"], "value") else fields["status"],
                "priority": fields["priority"].value if hasattr(fields["priority"], "value") else fields["priority"],
                "category": fields["category"],
            })
            updated += 1
        else:
            # Create new task
            task = Task(
                notion_id=notion_id,
                title=fields["title"],
                description=fields["description"],
                status=fields["status"],
                priority=fields["priority"],
                category=fields["category"],
            )
            await task_repo.create(task)
            created += 1

    return {"created": created, "updated": updated, "total": len(pages)}


async def sync_to_notion(task_id: str):
    """Push task status/priority changes to Notion."""
    if not settings.notion_api_key:
        return

    task = await task_repo.get(task_id)
    if not task or not task.notion_id:
        return

    STATUS_TO_NOTION = {v: k for k, v in NOTION_TO_STATUS.items()}
    PRIORITY_TO_NOTION = {v: k for k, v in NOTION_TO_PRIORITY.items()}

    headers = {**_HEADERS, "Authorization": f"Bearer {settings.notion_api_key}"}
    page_id = task.notion_id
    url = f"https://api.notion.com/v1/pages/{page_id}"

    body = {"properties": {
        "Status": {"select": {"name": STATUS_TO_NOTION.get(task.status, "Backlog")}},
        "Priority": {"select": {"name": PRIORITY_TO_NOTION.get(task.priority, "P2")}},
    }}

    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.patch(url, headers=headers, json=body)


async def run_sync_job():
    """Full bidirectional sync job."""
    result = await sync_from_notion()
    return result
