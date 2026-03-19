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

import httpx

from app.config import settings
from app.domain.models import Task

logger = logging.getLogger("task_approval_hook")

MAX_RETRIES = 2
RETRY_BACKOFF = [1.0, 2.0]  # seconds between retries


def _build_agent_message(task: Task) -> str:
    return (
        "[DASHBOARD TASK APPROVED]\n"
        f"Task ID: {task.id}\n"
        f"Title: {task.title}\n"
        f"Priority: {task.priority}\n"
        f"Executor Agent: {task.executor_agent or 'not assigned'}\n"
        f"Plan: {task.plan or 'no plan provided'}\n"
        f"Description: {task.description or 'no description'}\n"
        "\n"
        "This task was approved via the dashboard UI. "
        "Read the full task context from the Dashboard API if needed, "
        "then delegate execution to the appropriate agent according to the plan. "
        "Report results back when complete."
    )


async def _post_to_gateway(task: Task) -> bool:
    """POST chat completion to Gateway. Returns True on success."""
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
                return True
        except Exception as exc:
            logger.warning(
                "Gateway webhook attempt %d/%d failed for task %s: %s",
                attempt + 1, MAX_RETRIES + 1, task.id, exc,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF[attempt])

    return False


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

    success = await _post_to_gateway(task)

    if not success:
        logger.error(
            "All webhook retries exhausted for task %s — rolling back", task.id
        )
        await _rollback_task(task.id)

        # Emit a warning event
        try:
            from app.services.event_service import emit_event
            from app.domain.enums import EventSource

            await emit_event(
                "task.webhook_failed",
                title=(
                    f"⚠️ Approve failed for '{task.title}' — "
                    "could not reach agent runtime. Task returned to Planned."
                ),
                task_id=task.id,
                agent_id=task.executor_agent,
                source=EventSource.system,
                data={
                    "error": "Gateway webhook unreachable after retries",
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
