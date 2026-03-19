from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any

from app.domain.models import Artifact
from app.storage.json_store import read_json, write_json
from app.config import settings


class ArtifactRepository:
    def __init__(self):
        self._index: dict[str, dict] = {}
        self._loaded = False

    def _data_dir(self) -> Path:
        return Path(settings.data_dir) / "artifacts"

    def _artifact_path(self, artifact_id: str) -> Path:
        return self._data_dir() / f"{artifact_id}.json"

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

    async def get(self, artifact_id: str) -> Artifact | None:
        raw = read_json(self._artifact_path(artifact_id))
        if raw is None:
            return None
        return Artifact(**raw)

    async def list(
        self,
        task_id: str | None = None,
        session_id: str | None = None,
    ) -> list[Artifact]:
        self._load_index()
        results = []
        for aid, entry in self._index.items():
            if task_id and entry.get("task_id") != task_id:
                continue
            if session_id and entry.get("session_id") != session_id:
                continue
            a = await self.get(aid)
            if a:
                results.append(a)
        return results

    async def create(self, artifact: Artifact) -> Artifact:
        self._load_index()
        data = artifact.model_dump(mode="json")
        write_json(self._artifact_path(artifact.id), data)
        self._index[artifact.id] = {
            "task_id": artifact.task_id,
            "session_id": artifact.session_id,
            "filename": artifact.filename,
            "created_at": data["created_at"],
        }
        self._save_index()
        return artifact

    async def delete(self, artifact_id: str) -> bool:
        self._load_index()
        path = self._artifact_path(artifact_id)
        if not path.exists():
            return False
        path.unlink()
        self._index.pop(artifact_id, None)
        self._save_index()
        return True


artifact_repo = ArtifactRepository()
