"""
Task Approval Hook — triggers an OpenClaw Gateway chat completion
when a task is approved+confirmed (approved=True, status=in_progress).

Flow:
  1. Build message with task context
  2. POST to Gateway Chat Completions (model: openclaw:main)
  3. On failure (after retries): rollback status to planned, keep approved=True
"""
import asyncio
import logging
from typing import Optional, Tuple

import httpx

from app.config import settings
from app.domain.models import Task

logger = logging.getLogger("task_approval_hook")

MAX_RETRIES = 2
RETRY_BACKOFF = [1.0, 2.0]  # seconds between retries


def _build_agent_message(task: Task) -> str:
    """
    Stable dashboard -> main approval contract (v1).

    Design goals:
    - Explicit task_id for context recovery in any session
    - Compact, line-oriented format (human + machine friendly)
    - Durable keys for downstream parsing
    """
    metadata = (task.runtime_metadata or {}).get("dashboard_approval", {})
    return (
        f"Approve Task: {task.title}\n"
        "contract: dashboard.approval.v1\n"
        f"task_id: {task.id}\n"
        f"title: {task.title}\n"
        f"priority: {task.priority}\n"
        f"executor_agent: {task.executor_agent or 'unassigned'}\n"
        f"plan: {task.plan or '-'}\n"
        f"description: {task.description or '-'}\n"
        f"report_back_session: {metadata.get('report_back_session') or 'unknown'}\n"
        f"report_back_channel: {metadata.get('report_back_channel') or 'unknown'}\n"
        f"report_back_chat_id: {metadata.get('report_back_chat_id') or 'unknown'}\n"
        f"main_session_id: {metadata.get('main_session_id') or 'unknown'}\n"
        f"executor_session_id: {metadata.get('executor_session_id') or 'unknown'}\n"
        "execution_context_required: true\n"
        "source: dashboard_ui\n"
        "action: fetch_task_context_by_id_and_execute"
    )


async def _post_to_gateway(task: Task) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    POST chat completion to Gateway.

    Returns:
      (success, failure_kind, failure_detail)
    where failure_kind is one of:
      - auth: 401/403 from Gateway
      - timeout: request timed out
      - network: request could not reach Gateway
      - http: non-auth HTTP error from Gateway
      - unknown: unexpected failure
    """
    url = f"{settings.openclaw_gateway_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openclaw_gateway_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openclaw:main",
        "messages": [
            {"role": "user", "content": _build_agent_message(task)},
        ],
        "stream": False,
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                logger.info(
                    "Gateway webhook succeeded for task %s (attempt %d)",
                    task.id, attempt + 1,
                )
                return True, None, None
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            detail = f"HTTP {status_code}: {exc.response.text[:300]}"
            if status_code in (401, 403):
                logger.error(
                    "Gateway auth failed for task %s (attempt %d): %s",
                    task.id, attempt + 1, detail,
                )
                return False, "auth", detail

            logger.warning(
                "Gateway webhook HTTP error attempt %d/%d for task %s: %s",
                attempt + 1, MAX_RETRIES + 1, task.id, detail,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF[attempt])
            else:
                return False, "http", detail
        except httpx.TimeoutException as exc:
            detail = str(exc)
            logger.warning(
                "Gateway webhook timeout attempt %d/%d for task %s: %s",
                attempt + 1, MAX_RETRIES + 1, task.id, detail,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF[attempt])
            else:
                return False, "timeout", detail
        except httpx.RequestError as exc:
            detail = str(exc)
            logger.warning(
                "Gateway webhook network error attempt %d/%d for task %s: %s",
                attempt + 1, MAX_RETRIES + 1, task.id, detail,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF[attempt])
            else:
                return False, "network", detail
        except Exception as exc:
            detail = str(exc)
            logger.warning(
                "Gateway webhook unexpected error attempt %d/%d for task %s: %s",
                attempt + 1, MAX_RETRIES + 1, task.id, detail,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF[attempt])
            else:
                return False, "unknown", detail

    return False, "unknown", "retries exhausted"


async def _rollback_task(task_id: str):
    """Rollback task status to planned on webhook failure."""
    # Import here to avoid circular imports
    from app.storage.task_repo import task_repo

    await task_repo.update(task_id, {
        "status": "planned",
        "sub_status": None,
    })
    logger.warning(
        "Task %s rolled back to planned after webhook failure", task_id
    )


async def trigger_approval_hook(task: Task):
    """
    Fire-and-forget: POST to Gateway, rollback on failure.
    Called as a background asyncio task.
    """
    logger.info("Triggering approval hook for task %s (%s)", task.id, task.title)

    approval_context = (task.runtime_metadata or {}).get("dashboard_approval", {})
    if not approval_context.get("report_back_session") or not approval_context.get("report_back_channel"):
        logger.error("Missing mandatory report-back context for task %s", task.id)
        await _rollback_task(task.id)
        try:
            from app.services.event_service import emit_event
            from app.domain.enums import EventSource

            await emit_event(
                "task.approval_context_missing",
                title=(
                    f"⚠️ Approve failed for '{task.title}' — missing report-back target. "
                    "Task returned to Planned."
                ),
                task_id=task.id,
                agent_id=task.executor_agent,
                source=EventSource.system,
                data={"rollback_to": "planned", "missing": ["report_back_session", "report_back_channel"]},
            )
        except Exception as exc:
            logger.error("Failed to emit missing-context event: %s", exc)
        return

    success, failure_kind, failure_detail = await _post_to_gateway(task)

    if not success:
        logger.error(
            "Webhook failed for task %s (%s) — rolling back",
            task.id,
            failure_kind,
        )
        await _rollback_task(task.id)

        # Emit a warning event
        try:
            from app.services.event_service import emit_event
            from app.domain.enums import EventSource

            is_auth_failure = failure_kind == "auth"
            failure_message = (
                "Gateway webhook rejected credentials (401/403)"
                if is_auth_failure
                else "Gateway webhook unreachable after retries"
            )
            title_suffix = (
                "agent auth failed"
                if is_auth_failure
                else "could not reach agent runtime"
            )

            await emit_event(
                "task.webhook_failed",
                title=(
                    f"⚠️ Approve failed for '{task.title}' — "
                    f"{title_suffix}. Task returned to Planned."
                ),
                task_id=task.id,
                agent_id=task.executor_agent,
                source=EventSource.system,
                data={
                    "error": failure_message,
                    "failure_kind": failure_kind,
                    "failure_detail": failure_detail,
                    "rollback_to": "planned",
                },
            )
        except Exception as exc:
            logger.error("Failed to emit warning event: %s", exc)


def schedule_approval_hook(task: Task):
    """
    Schedule the approval hook as a background asyncio task.
    Does not block the caller.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(trigger_approval_hook(task))
        logger.info("Scheduled approval hook for task %s", task.id)
    except RuntimeError:
        logger.error("No running event loop — cannot schedule approval hook")
