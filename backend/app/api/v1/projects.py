from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, HTTPException, Depends

from app.core.deps import get_current_user
from app.domain.models import Project, ProjectCreate, ProjectUpdate
from app.storage.json_store import read_json, write_json
from app.config import settings

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectRepository:
    def __init__(self):
        self._index: dict[str, dict] = {}
        self._loaded = False

    def _data_dir(self) -> Path:
        return Path(settings.data_dir) / "projects"

    def _project_path(self, project_id: str) -> Path:
        return self._data_dir() / f"{project_id}.json"

    def _index_path(self) -> Path:
        return self._data_dir() / "index.json"

    def _load(self):
        if self._loaded:
            return
        raw = read_json(self._index_path())
        self._index = raw if isinstance(raw, dict) else {}
        self._loaded = True

    def _save(self):
        write_json(self._index_path(), self._index)

    async def get(self, project_id: str) -> Project | None:
        raw = read_json(self._project_path(project_id))
        if raw is None:
            return None
        return Project(**raw)

    async def list(self) -> list[Project]:
        self._load()
        results = []
        for pid in self._index:
            p = await self.get(pid)
            if p:
                results.append(p)
        return results

    async def create(self, project: Project) -> Project:
        self._load()
        data = project.model_dump(mode="json")
        write_json(self._project_path(project.id), data)
        self._index[project.id] = {"title": project.title, "status": project.status}
        self._save()
        return project

    async def update(self, project_id: str, updates: dict[str, Any]) -> Project | None:
        project = await self.get(project_id)
        if project is None:
            return None
        data = project.model_dump(mode="json")
        data.update(updates)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        write_json(self._project_path(project_id), data)
        self._load()
        if project_id in self._index:
            self._index[project_id].update({k: v for k, v in updates.items() if k in self._index[project_id]})
            self._save()
        return Project(**data)

    async def delete(self, project_id: str) -> bool:
        self._load()
        path = self._project_path(project_id)
        if not path.exists():
            return False
        path.unlink()
        self._index.pop(project_id, None)
        self._save()
        return True


_repo = ProjectRepository()


@router.get("/")
async def list_projects(_user: str = Depends(get_current_user)):
    projects = await _repo.list()
    return [p.model_dump(mode="json") for p in projects]


@router.post("/", status_code=201)
async def create_project(data: ProjectCreate, _user: str = Depends(get_current_user)):
    project = Project(**data.model_dump())
    await _repo.create(project)
    return project.model_dump(mode="json")


@router.get("/{project_id}")
async def get_project(project_id: str, _user: str = Depends(get_current_user)):
    project = await _repo.get(project_id)
    if project is None:
        raise HTTPException(404, f"Project {project_id} not found")
    return project.model_dump(mode="json")


@router.patch("/{project_id}")
async def patch_project(project_id: str, data: ProjectUpdate, _user: str = Depends(get_current_user)):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = await _repo.update(project_id, updates)
    if updated is None:
        raise HTTPException(404, f"Project {project_id} not found")
    return updated.model_dump(mode="json")


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, _user: str = Depends(get_current_user)):
    deleted = await _repo.delete(project_id)
    if not deleted:
        raise HTTPException(404, f"Project {project_id} not found")
