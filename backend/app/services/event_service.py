from datetime import datetime, timezone
from typing import Any

from app.domain.models import Event
from app.domain.enums import EventSource
from app.storage.event_repo import event_repo
from app.core.event_bus import event_bus


async def emit_event(
    event_type: str,
    title: str = "",
    task_id: str | None = None,
    session_id: str | None = None,
    agent_id: str | None = None,
    source: EventSource = EventSource.system,
    data: dict[str, Any] | None = None,
) -> Event:
    """Create, persist, and publish an event."""
    event = Event(
        type=event_type,
        title=title or event_type,
        task_id=task_id,
        session_id=session_id,
        agent_id=agent_id,
        source=source,
        data=data or {},
        timestamp=datetime.now(timezone.utc),
    )
    await event_repo.append(event)
    await event_bus.publish(event.model_dump(mode="json"))
    return event
