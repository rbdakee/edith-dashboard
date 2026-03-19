from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from app.domain.models import Agent
from app.domain.enums import AgentStatus
from app.storage.json_store import read_json, write_json
from app.config import settings

# Seed data from CLAUDE.md section E
AGENT_SEED = [
    {
        "id": "main",
        "name": "E.D.I.T.H.",
        "model": "openai-codex/gpt-5.4",
        "skills": ["orchestrator", "memory-manager", "activity-logger"],
        "status": "idle",
        "current_task_id": None,
        "current_session_id": None,
        "last_active_at": None,
    },
    {
        "id": "edith-routine",
        "name": "E.D.I.T.H. Routine",
        "model": "openai-codex/gpt-5.1-codex-mini",
        "skills": ["task-manager", "notion-task-manager", "notion-finance-analyst", "notion-fitness-analyst", "prayer-times"],
        "status": "idle",
        "current_task_id": None,
        "current_session_id": None,
        "last_active_at": None,
    },
    {
        "id": "edith-dev",
        "name": "E.D.I.T.H. Dev",
        "model": "openai-codex/gpt-5.3-codex",
        "skills": ["backend-dev", "frontend-dev", "designer", "project-planner", "autonomous-builder", "git-manager"],
        "status": "idle",
        "current_task_id": None,
        "current_session_id": None,
        "last_active_at": None,
    },
    {
        "id": "edith-analytics",
        "name": "E.D.I.T.H. Analytics",
        "model": "openai-codex/gpt-5.1-codex-mini",
        "skills": ["data-analytics"],
        "status": "idle",
        "current_task_id": None,
        "current_session_id": None,
        "last_active_at": None,
    },
    {
        "id": "edith-orchestrator",
        "name": "E.D.I.T.H. Orchestrator",
        "model": "openai-codex/gpt-5.3-codex",
        "skills": ["orchestrator", "project-planner", "activity-logger", "memory-manager"],
        "status": "idle",
        "current_task_id": None,
        "current_session_id": None,
        "last_active_at": None,
    },
]


class AgentRepository:
    """JSON-backed agent repository. All agents stored in agents/state.json."""

    def __init__(self):
        self._agents: dict[str, dict] = {}
        self._loaded = False

    def _state_path(self) -> Path:
        return Path(settings.data_dir) / "agents" / "state.json"

    def _load(self):
        if self._loaded:
            return
        raw = read_json(self._state_path())
        if raw is None:
            # Seed from defaults
            self._agents = {a["id"]: a for a in AGENT_SEED}
            self._save()
        else:
            self._agents = raw if isinstance(raw, dict) else {a["id"]: a for a in (raw if isinstance(raw, list) else AGENT_SEED)}
        self._loaded = True

    def _save(self):
        write_json(self._state_path(), self._agents)

    async def get(self, agent_id: str) -> Agent | None:
        self._load()
        data = self._agents.get(agent_id)
        if data is None:
            return None
        return Agent(**data)

    async def list(self) -> list[Agent]:
        self._load()
        return [Agent(**data) for data in self._agents.values()]

    async def update(self, agent_id: str, updates: dict[str, Any]) -> Agent | None:
        self._load()
        if agent_id not in self._agents:
            return None
        self._agents[agent_id].update(updates)
        if "last_active_at" not in updates:
            self._agents[agent_id]["last_active_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        return Agent(**self._agents[agent_id])

    async def seed_if_empty(self):
        """Ensure agents are seeded on first startup."""
        self._load()


agent_repo = AgentRepository()
