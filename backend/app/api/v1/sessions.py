from fastapi import APIRouter, HTTPException, Query, Depends

from app.core.deps import get_current_user
from app.domain.models import Session, SessionCreate, SessionUpdate
from app.storage.session_repo import session_repo
from app.services.session_service import create_session
from app.services.openclaw_session_truth import reconcile_sessions_with_openclaw_truth
from app.config import settings
from app.services.main_session_presence import is_current_main_telegram_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/")
async def list_sessions(
    agent_id: str | None = Query(None),
    task_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    _user: str = Depends(get_current_user),
):
    # Keep dashboard view close to real OpenClaw state on every list call.
    await reconcile_sessions_with_openclaw_truth(settings.openclaw_dir, stale_seconds=30)

    sessions = await session_repo.list(
        agent_id=agent_id,
        task_id=task_id,
        status=status,
        limit=limit,
    )

    # Keep all session semantics intact, but hide only the currently open
    # main direct Telegram session from Sessions API consumers.
    filtered_sessions = [
        s for s in sessions
        if not (s.status == "active" and is_current_main_telegram_session(s))
    ]
    return [s.model_dump(mode="json") for s in filtered_sessions]


@router.post("/", status_code=201)
async def create_session_endpoint(
    data: SessionCreate,
    _user: str = Depends(get_current_user),
):
    session = await create_session(data)
    return session.model_dump(mode="json")


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    _user: str = Depends(get_current_user),
):
    session = await session_repo.get(session_id)
    if session is None:
        raise HTTPException(404, f"Session {session_id} not found")
    return session.model_dump(mode="json")


@router.patch("/{session_id}")
async def patch_session(
    session_id: str,
    data: SessionUpdate,
    _user: str = Depends(get_current_user),
):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = await session_repo.update(session_id, updates)
    if updated is None:
        raise HTTPException(404, f"Session {session_id} not found")
    return updated.model_dump(mode="json")
