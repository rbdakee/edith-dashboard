from datetime import datetime, timezone

from app.domain.models import Session, SessionCreate, SessionUpdate
from app.domain.enums import SessionStatus, EventSource
from app.storage.session_repo import session_repo
from app.services.event_service import emit_event


async def create_session(data: SessionCreate) -> Session:
    session = Session(**data.model_dump())
    await session_repo.create(session)
    await emit_event(
        "session.started",
        title=f"Session started for agent {session.agent_id}",
        session_id=session.id,
        agent_id=session.agent_id,
        task_id=session.task_id,
        source=EventSource.system,
    )
    return session


async def complete_session(session_id: str) -> Session | None:
    now = datetime.now(timezone.utc)
    updated = await session_repo.update(session_id, {
        "status": SessionStatus.completed,
        "ended_at": now.isoformat(),
    })
    if updated:
        await emit_event(
            "session.completed",
            title=f"Session {session_id} completed",
            session_id=session_id,
            agent_id=updated.agent_id,
            source=EventSource.system,
        )
    return updated
