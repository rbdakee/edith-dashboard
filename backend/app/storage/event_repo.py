from __future__ import annotations

from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Any
import asyncio

from app.domain.models import Event
from app.storage.json_store import read_json, write_json, append_jsonl, read_jsonl
from app.config import settings


class EventRepository:
    """JSONL-backed event repository."""

    def __init__(self):
        # Serialize append() to avoid read-modify-write races on index.json
        # and reduce concurrent replace() pressure on Windows.
        self._append_lock = asyncio.Lock()

    def _data_dir(self) -> Path:
        return Path(settings.data_dir) / "events"

    def _day_path(self, day: date) -> Path:
        return self._data_dir() / day.isoformat() / "events.jsonl"

    def _index_path(self) -> Path:
        return self._data_dir() / "index.json"

    async def append(self, event: Event) -> Event:
        async with self._append_lock:
            data = event.model_dump(mode="json")
            ts = event.timestamp
            if isinstance(ts, str):
                day = date.fromisoformat(ts[:10])
            else:
                day = ts.date()
            append_jsonl(self._day_path(day), data)
            # Update rolling index (last 1000)
            index_raw = read_json(self._index_path())
            index = index_raw if isinstance(index_raw, list) else []
            index.append({
                "id": event.id,
                "type": event.type,
                "agent_id": event.agent_id,
                "task_id": event.task_id,
                "session_id": event.session_id,
                "source": event.source,
                "title": event.title,
                "timestamp": data["timestamp"],
            })
            # Keep last 1000
            if len(index) > 1000:
                index = index[-1000:]
            write_json(self._index_path(), index)
            return event

    async def list(
        self,
        task_id: str | None = None,
        agent_id: str | None = None,
        event_type: str | None = None,
        session_id: str | None = None,
        days_back: int = 7,
        limit: int = 50,
    ) -> list[dict]:
        results: list[dict] = []
        today = date.today()
        for i in range(days_back):
            day = today - timedelta(days=i)
            records = read_jsonl(self._day_path(day))
            for r in reversed(records):
                if task_id and r.get("task_id") != task_id:
                    continue
                if agent_id and r.get("agent_id") != agent_id:
                    continue
                if event_type and r.get("type") != event_type:
                    continue
                if session_id and r.get("session_id") != session_id:
                    continue
                results.append(r)
                if len(results) >= limit:
                    return results
        return results

    async def get_index(self, limit: int = 100) -> list[dict]:
        index_raw = read_json(self._index_path())
        index = index_raw if isinstance(index_raw, list) else []
        return list(reversed(index[-limit:]))


event_repo = EventRepository()
