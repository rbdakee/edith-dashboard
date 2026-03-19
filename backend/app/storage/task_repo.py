from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from app.domain.models import Task
from app.storage.json_store import read_json, write_json
from app.config import settings


class TaskRepository:
    """JSON-backed task repository with in-memory index cache."""

    def __init__(self):
        self._index: dict[str, dict] = {}
        self._cache: dict[str, dict] = {}
        self._loaded = False

    def _data_dir(self) -> Path:
        return Path(settings.data_dir) / "tasks"

    def _task_path(self, task_id: str) -> Path:
        return self._data_dir() / f"{task_id}.json"

    def _index_path(self) -> Path:
        return self._data_dir() / "index.json"

    def _load_index(self):
        if self._loaded:
            return
        raw = read_json(self._index_path())
        self._index = raw if isinstance(raw, dict) else {}
        self._loaded = True

    def _save_index(self):
        write_json(self._index_path(), self._index)

    def _index_entry(self, task: Task) -> dict:
        return {
            "title": task.title,
            "status": task.status,
            "executor_agent": task.executor_agent,
            "priority": task.priority,
            "category": task.category,
            "project_id": task.project_id,
            "parent_task_id": task.parent_task_id,
            "updated_at": task.updated_at.isoformat() if isinstance(task.updated_at, datetime) else task.updated_at,
        }

    async def get(self, task_id: str) -> Task | None:
        self._load_index()
        if task_id in self._cache:
            return Task(**self._cache[task_id])
        raw = read_json(self._task_path(task_id))
        if raw is None:
            return None
        self._cache[task_id] = raw
        return Task(**raw)

    async def list(
        self,
        status: str | None = None,
        priority: str | None = None,
        executor_agent: str | None = None,
        project_id: str | None = None,
        parent_task_id: str | None = None,
        top_level_only: bool = False,
    ) -> list[Task]:
        self._load_index()
        results = []
        for task_id, entry in self._index.items():
            if status and entry.get("status") != status:
                continue
            if priority and entry.get("priority") != priority:
                continue
            if executor_agent and entry.get("executor_agent") != executor_agent:
                continue
            if project_id and entry.get("project_id") != project_id:
                continue
            if top_level_only and entry.get("parent_task_id") is not None:
                continue
            if parent_task_id is not None and entry.get("parent_task_id") != parent_task_id:
                continue
            task = await self.get(task_id)
            if task:
                results.append(task)
        return results

    async def create(self, task: Task) -> Task:
        self._load_index()
        data = task.model_dump(mode="json")
        write_json(self._task_path(task.id), data)
        self._cache[task.id] = data
        self._index[task.id] = self._index_entry(task)
        self._save_index()
        return task

    async def update(self, task_id: str, updates: dict[str, Any]) -> Task | None:
        task = await self.get(task_id)
        if task is None:
            return None
        data = task.model_dump(mode="json")
        data.update(updates)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        write_json(self._task_path(task_id), data)
        self._cache[task_id] = data
        updated_task = Task(**data)
        self._index[task_id] = self._index_entry(updated_task)
        self._save_index()
        return updated_task

    async def delete(self, task_id: str) -> bool:
        self._load_index()
        path = self._task_path(task_id)
        if not path.exists():
            return False
        path.unlink()
        self._cache.pop(task_id, None)
        self._index.pop(task_id, None)
        self._save_index()
        return True

    async def get_index(self) -> dict[str, dict]:
        self._load_index()
        return dict(self._index)


task_repo = TaskRepository()
