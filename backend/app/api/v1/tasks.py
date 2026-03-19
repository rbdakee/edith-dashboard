from fastapi import APIRouter, HTTPException, Query, Depends

from app.core.deps import get_current_user
from app.domain.models import Task, TaskCreate, TaskUpdate
from app.storage.task_repo import task_repo
from app.services.task_service import create_task, update_task, approve_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/")
async def list_tasks(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    executor_agent: str | None = Query(None),
    project_id: str | None = Query(None),
    parent_task_id: str | None = Query(None),
    _user: str = Depends(get_current_user),
):
    tasks = await task_repo.list(
        status=status,
        priority=priority,
        executor_agent=executor_agent,
        project_id=project_id,
        parent_task_id=parent_task_id,
    )
    return [t.model_dump(mode="json") for t in tasks]


@router.post("/", status_code=201)
async def create_task_endpoint(
    data: TaskCreate,
    _user: str = Depends(get_current_user),
):
    task = await create_task(data)
    return task.model_dump(mode="json")


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    _user: str = Depends(get_current_user),
):
    task = await task_repo.get(task_id)
    if task is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return task.model_dump(mode="json")


@router.patch("/{task_id}")
async def patch_task(
    task_id: str,
    data: TaskUpdate,
    _user: str = Depends(get_current_user),
):
    updated = await update_task(task_id, data)
    if updated is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return updated.model_dump(mode="json")


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    _user: str = Depends(get_current_user),
):
    deleted = await task_repo.delete(task_id)
    if not deleted:
        raise HTTPException(404, f"Task {task_id} not found")


@router.post("/{task_id}/approve")
async def approve_task_endpoint(
    task_id: str,
    _user: str = Depends(get_current_user),
):
    updated = await approve_task(task_id)
    if updated is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return updated.model_dump(mode="json")
