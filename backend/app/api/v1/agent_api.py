"""
Agent API — API-key authenticated endpoints for OpenClaw agents.
Agents use X-API-Key header with the ingest_api_key value.
"""
from fastapi import APIRouter, HTTPException, Header
from pathlib import Path

from app.config import settings
from app.storage.json_store import read_json
from app.domain.models import TaskCreate, TaskUpdate, TaskExecutionReport
from app.storage.task_repo import task_repo
from app.storage.session_repo import session_repo
from app.storage.comment_repo import comment_repo
from app.services.task_service import create_task, update_task
from app.services.task_runtime import apply_execution_outcome
from app.services.comment_router import mark_delivered

router = APIRouter(prefix="/agent", tags=["agent-api"])


def _verify_agent_key(x_api_key: str = Header()):
    config = read_json(Path(settings.data_dir) / "config" / "auth.json")
    expected = config.get("ingest_api_key", "") if config else ""
    if not expected or x_api_key != expected:
        raise HTTPException(403, "Invalid API key")


# ── Tasks ────────────────────────────────────────────────────────────────────

@router.get("/tasks")
async def agent_list_tasks(
    status: str | None = None,
    x_api_key: str = Header(),
):
    _verify_agent_key(x_api_key)
    tasks = await task_repo.list(status=status)
    return [t.model_dump(mode="json") for t in tasks]


@router.post("/tasks", status_code=201)
async def agent_create_task(data: TaskCreate, x_api_key: str = Header()):
    _verify_agent_key(x_api_key)
    task = await create_task(data)
    return task.model_dump(mode="json")


@router.patch("/tasks/{task_id}")
async def agent_update_task(task_id: str, data: TaskUpdate, x_api_key: str = Header()):
    _verify_agent_key(x_api_key)
    updated = await update_task(task_id, data)
    if updated is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return updated.model_dump(mode="json")


@router.get("/tasks/{task_id}")
async def agent_get_task(task_id: str, x_api_key: str = Header()):
    _verify_agent_key(x_api_key)
    task = await task_repo.get(task_id)
    if task is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return task.model_dump(mode="json")


@router.post("/tasks/{task_id}/execution-report")
async def agent_report_task_execution(
    task_id: str,
    payload: TaskExecutionReport,
    x_api_key: str = Header(),
):
    _verify_agent_key(x_api_key)
    updated = await apply_execution_outcome(
        task_id=task_id,
        success=payload.success,
        summary=payload.summary,
        error=payload.error,
        main_session_id=payload.main_session_id,
        executor_session_id=payload.executor_session_id,
        report_back_session=payload.report_back_session,
        report_back_channel=payload.report_back_channel,
        report_back_chat_id=payload.report_back_chat_id,
    )
    if updated is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return updated.model_dump(mode="json")


# ── Sessions ──────────────────────────────────────────────────────────────────

@router.get("/sessions")
async def agent_list_sessions(
    agent_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
    x_api_key: str = Header(),
):
    _verify_agent_key(x_api_key)
    sessions = await session_repo.list(agent_id=agent_id, status=status, limit=limit)
    return [s.model_dump(mode="json") for s in sessions]


@router.get("/sessions/{session_id}")
async def agent_get_session(session_id: str, x_api_key: str = Header()):
    _verify_agent_key(x_api_key)
    s = await session_repo.get(session_id)
    if s is None:
        raise HTTPException(404, f"Session {session_id} not found")
    return s.model_dump(mode="json")


# ── Comments ──────────────────────────────────────────────────────────────────

@router.get("/comments")
async def agent_get_comments(
    routed_to: str | None = None,
    x_api_key: str = Header(),
):
    _verify_agent_key(x_api_key)
    comments = await comment_repo.list(routed_to=routed_to, delivered=False)
    return [c.model_dump(mode="json") for c in comments]


@router.patch("/comments/{comment_id}/deliver")
async def agent_deliver_comment(comment_id: str, x_api_key: str = Header()):
    _verify_agent_key(x_api_key)
    updated = await mark_delivered(comment_id)
    if updated is None:
        raise HTTPException(404, f"Comment {comment_id} not found")
    return updated.model_dump(mode="json")
