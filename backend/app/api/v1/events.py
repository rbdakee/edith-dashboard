from fastapi import APIRouter, HTTPException, Header, Query, Depends
from pydantic import BaseModel
from typing import Any
from datetime import datetime, timezone
import uuid

from app.core.event_bus import event_bus
from app.core.deps import get_current_user
from app.storage.json_store import read_json
from app.storage.event_repo import event_repo
from app.domain.models import Event
from app.domain.enums import EventSource
from app.config import settings

router = APIRouter(prefix="/events", tags=["events"])


class IngestEvent(BaseModel):
    type: str
    agent_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None
    timestamp: datetime | None = None
    data: dict[str, Any] = {}
    title: str | None = None


def _get_ingest_key() -> str:
    from pathlib import Path
    config = read_json(Path(settings.data_dir) / "config" / "auth.json")
    return config.get("ingest_api_key", "") if config else ""


@router.post("/ingest")
async def ingest_event(event: IngestEvent, x_api_key: str = Header()):
    """Receive events from OpenClaw hooks. Authed via API key."""
    expected = _get_ingest_key()
    if not expected or x_api_key != expected:
        raise HTTPException(403, "Invalid API key")

    normalized = Event(
        id=f"evt_{uuid.uuid4().hex[:12]}",
        type=event.type,
        agent_id=event.agent_id,
        session_id=event.session_id,
        task_id=event.task_id,
        timestamp=event.timestamp or datetime.now(timezone.utc),
        source=EventSource.hook,
        title=event.title or event.type,
        data=event.data,
    )

    await event_repo.append(normalized)
    await event_bus.publish(normalized.model_dump(mode="json"))

    return {"ok": True, "event_id": normalized.id}


@router.get("/")
async def list_events(
    task_id: str | None = Query(None),
    agent_id: str | None = Query(None),
    event_type: str | None = Query(None),
    session_id: str | None = Query(None),
    days_back: int = Query(7, ge=1, le=90),
    limit: int = Query(50, le=200),
    _user: str = Depends(get_current_user),
):
    """Query events with optional filters."""
    events = await event_repo.list(
        task_id=task_id,
        agent_id=agent_id,
        event_type=event_type,
        session_id=session_id,
        days_back=days_back,
        limit=limit,
    )
    return events


@router.get("/index")
async def get_event_index(
    limit: int = Query(100, le=1000),
    _user: str = Depends(get_current_user),
):
    """Get rolling index of recent events."""
    index = await event_repo.get_index(limit=limit)
    return index
