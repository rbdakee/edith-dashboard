from pathlib import Path
from datetime import datetime, timezone
import json

from app.domain.models import Comment
from app.storage.comment_repo import comment_repo
from app.services.event_service import emit_event
from app.domain.enums import EventSource
from app.config import settings


async def create_and_route_comment(comment: Comment) -> Comment:
    """Store comment and write pickup file if routed to an agent."""
    saved = await comment_repo.create(comment)

    await emit_event(
        "comment.created",
        title=f"Comment by {comment.author}",
        task_id=comment.task_id,
        source=EventSource.user,
        data={"comment_id": comment.id, "routed_to": comment.routed_to},
    )

    if comment.routed_to:
        _write_comment_pickup(comment)

    return saved


def _write_comment_pickup(comment: Comment):
    """Write comment pickup file to data/outbound/{agent_id}/comments/{comment_id}.json"""
    agent_id = comment.routed_to
    outbound_dir = Path(settings.data_dir) / "outbound" / agent_id / "comments"
    outbound_dir.mkdir(parents=True, exist_ok=True)

    pickup = {
        "type": "comment",
        "comment_id": comment.id,
        "task_id": comment.task_id,
        "author": comment.author,
        "content": comment.content,
        "created_at": comment.created_at.isoformat() if isinstance(comment.created_at, datetime) else comment.created_at,
        "routed_to": comment.routed_to,
        "fragment_refs": [f.model_dump() for f in comment.fragment_refs],
    }
    path = outbound_dir / f"{comment.id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pickup, f, indent=2, default=str, ensure_ascii=False)


async def mark_delivered(comment_id: str) -> Comment | None:
    now = datetime.now(timezone.utc)
    updated = await comment_repo.update(comment_id, {
        "delivered": True,
        "delivered_at": now.isoformat(),
    })
    if updated:
        await emit_event(
            "comment.delivered",
            title=f"Comment {comment_id} delivered",
            task_id=updated.task_id,
            source=EventSource.system,
            data={"comment_id": comment_id},
        )
    return updated
