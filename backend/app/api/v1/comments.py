from fastapi import APIRouter, HTTPException, Query, Depends

from app.core.deps import get_current_user
from app.domain.models import Comment, CommentCreate
from app.storage.comment_repo import comment_repo
from app.services.comment_router import create_and_route_comment, mark_delivered

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/")
async def list_comments(
    task_id: str | None = Query(None),
    artifact_id: str | None = Query(None),
    session_id: str | None = Query(None),
    routed_to: str | None = Query(None),
    delivered: bool | None = Query(None),
    _user: str = Depends(get_current_user),
):
    comments = await comment_repo.list(
        task_id=task_id,
        artifact_id=artifact_id,
        session_id=session_id,
        routed_to=routed_to,
        delivered=delivered,
    )
    return [c.model_dump(mode="json") for c in comments]


@router.post("/", status_code=201)
async def create_comment(
    data: CommentCreate,
    _user: str = Depends(get_current_user),
):
    comment = Comment(**data.model_dump())
    saved = await create_and_route_comment(comment)
    return saved.model_dump(mode="json")


@router.get("/{comment_id}")
async def get_comment(comment_id: str, _user: str = Depends(get_current_user)):
    comment = await comment_repo.get(comment_id)
    if comment is None:
        raise HTTPException(404, f"Comment {comment_id} not found")
    return comment.model_dump(mode="json")


@router.patch("/{comment_id}/deliver")
async def deliver_comment(comment_id: str, _user: str = Depends(get_current_user)):
    updated = await mark_delivered(comment_id)
    if updated is None:
        raise HTTPException(404, f"Comment {comment_id} not found")
    return updated.model_dump(mode="json")
