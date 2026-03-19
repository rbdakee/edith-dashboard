from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import json

from app.domain.models import Task, TaskCreate, TaskUpdate
from app.domain.enums import TaskStatus, EventSource
from app.storage.task_repo import task_repo
from app.services.event_service import emit_event
from app.services.task_approval_hook import schedule_approval_hook
from app.services.approval_context import resolve_report_back_context
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

    # Emit outcome event with report-back correlation when execution ends.
    _was_in_progress = old_task.status == TaskStatus.in_progress
    _ended_status = updated.status in (TaskStatus.done, TaskStatus.planned, TaskStatus.archive)
    if _was_in_progress and _ended_status:
        approval_context = (updated.runtime_metadata or {}).get("dashboard_approval", {})
        await emit_event(
            "task.execution_outcome",
            title=f"Task '{updated.title}' finished with status: {updated.status}",
            task_id=task_id,
            agent_id=updated.executor_agent,
            source=EventSource.system,
            data={
                "status": updated.status,
                "sub_status": updated.sub_status,
                "approval_context": approval_context,
            },
        )

    return updated


async def approve_task(task_id: str, report_back_context: dict[str, Any] | None = None) -> Task | None:
    task = await task_repo.get(task_id)
    if task is None:
        return None

    # Idempotency: skip if already approved and in_progress
    if task.approved and task.status == TaskStatus.in_progress:
        return task

    existing_context = (task.runtime_metadata or {}).get("dashboard_approval", {})
    fallback_context = await resolve_report_back_context() or {}

    # Merge by key (priority: explicit payload > resolved fallback > existing task context)
    resolved_context = {
        **({k: v for k, v in existing_context.items() if v is not None} if isinstance(existing_context, dict) else {}),
        **({k: v for k, v in fallback_context.items() if v is not None} if isinstance(fallback_context, dict) else {}),
        **({k: v for k, v in report_back_context.items() if v is not None} if isinstance(report_back_context, dict) else {}),
    }

    if not resolved_context:
        raise ValueError("Cannot approve task without report-back context: no context sources available")

    required_keys = ("report_back_session", "report_back_channel")
    missing_keys = [k for k in required_keys if not resolved_context.get(k)]
    if missing_keys:
        provided_keys = sorted([k for k, v in resolved_context.items() if v])
        raise ValueError(
            "Incomplete report-back context for approval; "
            f"missing={missing_keys}; provided={provided_keys}"
        )

    now = datetime.now(timezone.utc)
    runtime_metadata = dict(task.runtime_metadata or {})
    runtime_metadata.update({
        "task_id": task.id,
        "report_back_session": resolved_context.get("report_back_session"),
        "report_back_channel": resolved_context.get("report_back_channel"),
        "report_back_chat_id": resolved_context.get("report_back_chat_id"),
        "main_session_id": resolved_context.get("main_session_id"),
        "executor_session_id": resolved_context.get("executor_session_id"),
    })
    runtime_metadata["dashboard_approval"] = {
        "contract": "dashboard.approval.v1",
        "task_id": task.id,
        "source": "dashboard_ui",
        "action": "fetch_task_context_by_id_and_execute",
        **resolved_context,
        "approved_at": now.isoformat(),
    }

    updates = {
        "approved": True,
        "approved_at": now.isoformat(),
        "status": TaskStatus.in_progress,
        "last_status_change_at": now.isoformat(),
        "runtime_metadata": runtime_metadata,
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
        data={
            "approved_at": now.isoformat(),
            "executor_agent": updated.executor_agent,
            "approval_context": runtime_metadata.get("dashboard_approval", {}),
        },
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

    approval_context = (task.runtime_metadata or {}).get("dashboard_approval", {})

    pickup = {
        "type": "approval",
        "task_id": task.id,
        "task_title": task.title,
        "approved_at": approved_at.isoformat(),
        "approved_by": "user",
        "approval_context": approval_context,
        "delegation_packet": (
            f"[DELEGATED_BY: dashboard]\n"
            f"[TASK]: Task '{task.title}' has been approved. Begin execution.\n"
            f"[CONTEXT]: See task context at data/tasks/{task.id}_context.md\n"
            f"[EXPECTED OUTPUT]: status updates via dashboard event ingest API\n"
            f"[REPORT BACK]: required ({approval_context.get('report_back_channel', 'unknown')}:{approval_context.get('report_back_chat_id', '-')})"
        ),
    }
    path = outbound_dir / f"{task.id}_approved.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pickup, f, indent=2, default=str, ensure_ascii=False)
