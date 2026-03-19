from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any

from app.domain.models import Comment
from app.storage.json_store import read_json, write_json
from app.config import settings


class CommentRepository:
    def __init__(self):
        self._index: dict[str, dict] = {}
        self._loaded = False

    def _data_dir(self) -> Path:
        return Path(settings.data_dir) / "comments"

    def _comment_path(self, comment_id: str) -> Path:
        return self._data_dir() / f"{comment_id}.json"

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

    async def get(self, comment_id: str) -> Comment | None:
        raw = read_json(self._comment_path(comment_id))
        if raw is None:
            return None
        return Comment(**raw)

    async def list(
        self,
        task_id: str | None = None,
        artifact_id: str | None = None,
        session_id: str | None = None,
        routed_to: str | None = None,
        delivered: bool | None = None,
    ) -> list[Comment]:
        self._load_index()
        results = []
        for cid, entry in self._index.items():
            if task_id and entry.get("task_id") != task_id:
                continue
            if artifact_id and entry.get("artifact_id") != artifact_id:
                continue
            if session_id and entry.get("session_id") != session_id:
                continue
            if routed_to and entry.get("routed_to") != routed_to:
                continue
            if delivered is not None and entry.get("delivered") != delivered:
                continue
            c = await self.get(cid)
            if c:
                results.append(c)
        return results

    async def create(self, comment: Comment) -> Comment:
        self._load_index()
        data = comment.model_dump(mode="json")
        write_json(self._comment_path(comment.id), data)
        self._index[comment.id] = {
            "task_id": comment.task_id,
            "artifact_id": comment.artifact_id,
            "session_id": comment.session_id,
            "routed_to": comment.routed_to,
            "delivered": comment.delivered,
            "author": comment.author,
            "created_at": data["created_at"],
        }
        self._save_index()
        return comment

    async def update(self, comment_id: str, updates: dict[str, Any]) -> Comment | None:
        comment = await self.get(comment_id)
        if comment is None:
            return None
        data = comment.model_dump(mode="json")
        data.update(updates)
        write_json(self._comment_path(comment_id), data)
        self._load_index()
        if comment_id in self._index:
            self._index[comment_id].update({k: v for k, v in updates.items() if k in self._index[comment_id]})
            self._save_index()
        return Comment(**data)


comment_repo = CommentRepository()
