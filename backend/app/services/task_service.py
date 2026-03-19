from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import json

from app.domain.models import Task, TaskCreate, TaskUpdate
from app.domain.enums import TaskStatus, EventSource
from app.storage.task_repo import task_repo
from app.services.event_service import emit_event
from app.services.task_approval_hook import schedule_approval_hook
from app.config import settings


async def create_task(data: TaskCreate) -> Task:
    task = Task(**data.model_dump())
    await task_repo.create(task)
    await emit_event(
        "task.created",
        title=f"Task created: {task.title}",
        task_id=task.id,
        source=EventSource.user,
        data={"title": task.title, "status": task.status, "priority": task.priority},
    )
    return task


async def update_task(task_id: str, data: TaskUpdate) -> Task | None:
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    old_task = await task_repo.get(task_id)
    if old_task is None:
        return None

    updated = await task_repo.update(task_id, updates)
    if updated is None:
        return None

    # Emit status change event if status changed
    if "status" in updates and old_task.status != updated.status:
        await emit_event(
            "task.status_changed",
            title=f"Task '{updated.title}' status: {old_task.status} → {updated.status}",
            task_id=task_id,
            source=EventSource.user,
            data={"old_status": old_task.status, "new_status": updated.status},
        )
        await task_repo.update(task_id, {"last_status_change_at": datetime.now(timezone.utc).isoformat()})

    # Trigger approval hook if task just became approved + in_progress via PATCH
    _newly_approved = (
        "approved" in updates
        and updates["approved"] is True
        and not old_task.approved
    )
    _is_in_progress = updated.status == TaskStatus.in_progress
    if _newly_approved and _is_in_progress:
        schedule_approval_hook(updated)

    return updated


async def approve_task(task_id: str) -> Task | None:
    task = await task_repo.get(task_id)
    if task is None:
        return None

    # Idempotency: skip if already approved and in_progress
    if task.approved and task.status == TaskStatus.in_progress:
        return task

    now = datetime.now(timezone.utc)
    updates = {
        "approved": True,
        "approved_at": now.isoformat(),
        "status": TaskStatus.in_progress,
        "last_status_change_at": now.isoformat(),
    }
    updated = await task_repo.update(task_id, updates)
    if updated is None:
        return None

    # Emit approved event
    await emit_event(
        "task.approved",
        title=f"Task '{updated.title}' approved",
        task_id=task_id,
        agent_id=updated.executor_agent,
        source=EventSource.user,
        data={"approved_at": now.isoformat(), "executor_agent": updated.executor_agent},
    )

    # Write pickup file for agent
    if updated.executor_agent:
        _write_approval_pickup(updated, now)

    # Trigger Gateway webhook to start agent session
    schedule_approval_hook(updated)

    return updated


def _write_approval_pickup(task: Task, approved_at: datetime):
    """Write approval pickup file to data/outbound/{agent_id}/{task_id}_approved.json"""
    agent_id = task.executor_agent
    outbound_dir = Path(settings.data_dir) / "outbound" / agent_id
    outbound_dir.mkdir(parents=True, exist_ok=True)

    pickup = {
        "type": "approval",
        "task_id": task.id,
        "task_title": task.title,
        "approved_at": approved_at.isoformat(),
        "approved_by": "user",
        "delegation_packet": (
            f"[DELEGATED_BY: dashboard]\n"
            f"[TASK]: Task '{task.title}' has been approved. Begin execution.\n"
            f"[CONTEXT]: See task context at data/tasks/{task.id}_context.md\n"
            f"[EXPECTED OUTPUT]: status updates via dashboard event ingest API\n"
            f"[REPORT BACK]: no"
        ),
    }
    path = outbound_dir / f"{task.id}_approved.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pickup, f, indent=2, default=str, ensure_ascii=False)
