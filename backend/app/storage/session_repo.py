from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any

from app.domain.models import Session
from app.storage.json_store import read_json, write_json
from app.config import settings


class SessionRepository:
    """JSON-backed session repository."""

    def __init__(self):
        self._index: dict[str, dict] = {}
        self._cache: dict[str, dict] = {}
        self._loaded = False

    def _data_dir(self) -> Path:
        return Path(settings.data_dir) / "sessions"

    def _session_path(self, session_id: str) -> Path:
        return self._data_dir() / f"{session_id}.json"

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

    def _index_entry(self, session: Session) -> dict:
        return {
            "agent_id": session.agent_id,
            "task_id": session.task_id,
            "status": session.status,
            "started_at": session.started_at.isoformat() if isinstance(session.started_at, datetime) else session.started_at,
            "ended_at": session.ended_at.isoformat() if isinstance(session.ended_at, datetime) and session.ended_at else None,
        }

    async def get(self, session_id: str) -> Session | None:
        self._load_index()
        if session_id in self._cache:
            return Session(**self._cache[session_id])
        raw = read_json(self._session_path(session_id))
        if raw is None:
            return None
        self._cache[session_id] = raw
        return Session(**raw)

    async def list(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Session]:
        self._load_index()
        results = []
        for sid, entry in self._index.items():
            if agent_id and entry.get("agent_id") != agent_id:
                continue
            if task_id and entry.get("task_id") != task_id:
                continue
            if status and entry.get("status") != status:
                continue
            s = await self.get(sid)
            if s:
                results.append(s)
            if len(results) >= limit:
                break
        return results

    async def create(self, session: Session) -> Session:
        self._load_index()
        data = session.model_dump(mode="json")
        write_json(self._session_path(session.id), data)
        self._cache[session.id] = data
        self._index[session.id] = self._index_entry(session)
        self._save_index()
        return session

    async def update(self, session_id: str, updates: dict[str, Any]) -> Session | None:
        session = await self.get(session_id)
        if session is None:
            return None
        data = session.model_dump(mode="json")
        data.update(updates)
        write_json(self._session_path(session_id), data)
        self._cache[session_id] = data
        updated = Session(**data)
        self._index[session_id] = self._index_entry(updated)
        self._save_index()
        return updated

    async def find_by_openclaw_id(self, openclaw_session_id: str) -> Session | None:
        """Find a session by its OpenClaw session ID (UUID or session key)."""
        self._load_index()
        for sid in list(self._index.keys()):
            s = await self.get(sid)
            if s and s.openclaw_session_id == openclaw_session_id:
                return s
        return None

    async def delete(self, session_id: str) -> bool:
        self._load_index()
        path = self._session_path(session_id)
        if not path.exists():
            return False
        path.unlink()
        self._cache.pop(session_id, None)
        self._index.pop(session_id, None)
        self._save_index()
        return True


session_repo = SessionRepository()
