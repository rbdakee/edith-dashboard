from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.domain.enums import EventSource, SubStatus, TaskStatus
from app.domain.models import Session, Task
from app.services.event_service import emit_event
from app.services.main_session_presence import find_active_main_telegram_session
from app.storage.session_repo import session_repo
from app.storage.task_repo import task_repo


def _extract_chat_id_from_session_key(session_key: str | None) -> str | None:
    if not session_key:
        return None
    parts = session_key.split(":")
    return parts[-1] if len(parts) >= 5 else None


async def build_report_back_context() -> dict[str, str | None]:
    sessions = await session_repo.list(agent_id="main", status="active", limit=200)
    main_session = find_active_main_telegram_session(sessions)
    if main_session is None:
        return {
            "report_back_session": None,
            "report_back_channel": None,
            "report_back_chat_id": None,
            "main_session_id": None,
        }

    snapshot = main_session.context_snapshot or {}
    session_key = snapshot.get("session_key") or main_session.openclaw_session_id
    channel = snapshot.get("channel")
    chat_id = _extract_chat_id_from_session_key(session_key)

    return {
        "report_back_session": session_key,
        "report_back_channel": channel,
        "report_back_chat_id": chat_id,
        "main_session_id": main_session.id,
    }


def merge_runtime_metadata(current: dict[str, Any] | None, updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(current or {})
    for key, value in updates.items():
        if value is not None:
            merged[key] = value
    return merged


async def apply_execution_outcome(
    *,
    task_id: str,
    success: bool,
    summary: str | None = None,
    error: str | None = None,
    executor_session_id: str | None = None,
    main_session_id: str | None = None,
    report_back_session: str | None = None,
    report_back_channel: str | None = None,
    report_back_chat_id: str | None = None,
    source: EventSource = EventSource.system,
) -> Task | None:
    task = await task_repo.get(task_id)
    if task is None:
        return None

    now = datetime.now(timezone.utc).isoformat()
    status = TaskStatus.done if success else TaskStatus.planned
    sub_status = None if success else SubStatus.blocked

    runtime_metadata = merge_runtime_metadata(
        task.runtime_metadata,
        {
            "task_id": task.id,
            "main_session_id": main_session_id,
            "executor_session_id": executor_session_id,
            "report_back_session": report_back_session,
            "report_back_channel": report_back_channel,
            "report_back_chat_id": report_back_chat_id,
            "last_execution": {
                "at": now,
                "success": success,
                "summary": summary,
                "error": error,
            },
        },
    )

    updated = await task_repo.update(
        task.id,
        {
            "status": status,
            "sub_status": sub_status,
            "runtime_metadata": runtime_metadata,
            "last_status_change_at": now,
            "last_activity_at": now,
        },
    )

    if updated is None:
        return None

    event_type = "task.execution_completed" if success else "task.execution_failed"
    title = (
        f"Task '{updated.title}' completed"
        if success
        else f"Task '{updated.title}' failed"
    )
    await emit_event(
        event_type,
        title=title,
        task_id=updated.id,
        agent_id=updated.executor_agent,
        source=source,
        data={
            "summary": summary,
            "error": error,
            "main_session_id": main_session_id,
            "executor_session_id": executor_session_id,
            "report_back_session": report_back_session,
            "report_back_channel": report_back_channel,
            "report_back_chat_id": report_back_chat_id,
            "status": updated.status,
            "sub_status": updated.sub_status,
        },
    )

    await trigger_report_back_to_main(
        task=updated,
        success=success,
        summary=summary,
        error=error,
    )

    return updated


async def trigger_report_back_to_main(
    *,
    task: Task,
    success: bool,
    summary: str | None,
    error: str | None,
) -> None:
    metadata = task.runtime_metadata or {}
    report_back_session = metadata.get("report_back_session")
    report_back_channel = metadata.get("report_back_channel")
    report_back_chat_id = metadata.get("report_back_chat_id")

    if not report_back_session:
        return

    payload_lines = [
        "contract: dashboard.execution.report.v1",
        f"task_id: {task.id}",
        f"title: {task.title}",
        f"outcome: {'success' if success else 'failure'}",
        f"report_back_session: {report_back_session}",
        f"report_back_channel: {report_back_channel or 'unknown'}",
        f"report_back_chat_id: {report_back_chat_id or 'unknown'}",
        f"main_session_id: {metadata.get('main_session_id') or 'unknown'}",
        f"executor_session_id: {metadata.get('executor_session_id') or 'unknown'}",
        f"summary: {summary or '-'}",
        f"error: {error or '-'}",
        "action: send_report_back_to_originating_chat",
    ]

    url = f"{settings.openclaw_gateway_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openclaw_gateway_token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            await client.post(
                url,
                headers=headers,
                json={
                    "model": "openclaw:main",
                    "messages": [{"role": "user", "content": "\n".join(payload_lines)}],
                    "stream": False,
                },
            )
    except Exception:
        # Non-fatal: lifecycle update already persisted, chat report can be retried externally.
        return
