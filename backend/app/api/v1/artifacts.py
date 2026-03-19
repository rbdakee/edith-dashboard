from fastapi import APIRouter, HTTPException, Query, Depends

from app.core.deps import get_current_user
from app.domain.models import Artifact, ArtifactCreate
from app.storage.artifact_repo import artifact_repo

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/")
async def list_artifacts(
    task_id: str | None = Query(None),
    session_id: str | None = Query(None),
    _user: str = Depends(get_current_user),
):
    artifacts = await artifact_repo.list(task_id=task_id, session_id=session_id)
    return [a.model_dump(mode="json") for a in artifacts]


@router.post("/", status_code=201)
async def create_artifact(
    data: ArtifactCreate,
    _user: str = Depends(get_current_user),
):
    artifact = Artifact(**data.model_dump())
    saved = await artifact_repo.create(artifact)
    return saved.model_dump(mode="json")


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str, _user: str = Depends(get_current_user)):
    artifact = await artifact_repo.get(artifact_id)
    if artifact is None:
        raise HTTPException(404, f"Artifact {artifact_id} not found")
    return artifact.model_dump(mode="json")


@router.delete("/{artifact_id}", status_code=204)
async def delete_artifact(artifact_id: str, _user: str = Depends(get_current_user)):
    deleted = await artifact_repo.delete(artifact_id)
    if not deleted:
        raise HTTPException(404, f"Artifact {artifact_id} not found")
