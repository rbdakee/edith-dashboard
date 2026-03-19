from typing import Any

from app.domain.models import Comment, CommentCreate
from app.domain.enums import CommentAuthor


async def dispatch_client_message(msg: dict[str, Any]):
    """Dispatch incoming WebSocket messages to appropriate services."""
    msg_type = msg.get("type")

    if msg_type == "comment":
        await _handle_comment(msg.get("payload", {}))
    elif msg_type == "approve":
        await _handle_approve(msg.get("payload", {}))


async def _handle_comment(payload: dict[str, Any]):
    """Handle a comment message from the frontend."""
    from app.services.comment_router import create_and_route_comment

    task_id = payload.get("task_id")
    content = payload.get("content", "")
    routed_to = payload.get("routed_to")

    if not content:
        return

    comment = Comment(
        task_id=task_id,
        author=CommentAuthor.user,
        content=content,
        routed_to=routed_to,
    )
    await create_and_route_comment(comment)


async def _handle_approve(payload: dict[str, Any]):
    """Handle an approval message from the frontend."""
    from app.services.task_service import approve_task

    task_id = payload.get("task_id")
    if task_id:
        await approve_task(task_id)
