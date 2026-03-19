from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from app.domain.models import Agent
from app.domain.enums import AgentStatus
from app.storage.json_store import read_json, write_json
from app.config import settings

# Emergency fallback: used ONLY when OpenClaw config is unreachable AND state.json doesn't exist.
# In normal operation, agent list is synced from openclaw.json.
AGENT_SEED: list[dict[str, Any]] = []

# Fields owned by OpenClaw config (always overwritten on sync)
_CONFIG_OWNED_FIELDS = {"id", "name", "model", "skills"}

# Fields owned by dashboard (preserved during sync)
_DASHBOARD_OWNED_FIELDS = {
    "status", "current_task_id", "current_session_id",
    "current_session_context", "last_active_at",
}


def _idle_defaults() -> dict[str, Any]:
    """Default dashboard-owned fields for a new agent."""
    return {
        "status": "idle",
        "current_task_id": None,
        "current_session_id": None,
        "current_session_context": None,
        "last_active_at": None,
    }


class AgentRepository:
    """JSON-backed agent repository. Syncs agent definitions from OpenClaw config."""

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
            # No state.json — use AGENT_SEED as emergency fallback
            self._agents = {a["id"]: a for a in AGENT_SEED}
            if self._agents:
                self._save()
        else:
            self._agents = raw if isinstance(raw, dict) else {
                a["id"]: a for a in (raw if isinstance(raw, list) else AGENT_SEED)
            }
        self._loaded = True

    def _save(self):
        write_json(self._state_path(), self._agents)

    async def sync_from_config(self) -> dict[str, Any]:
        """
        Sync agent list from OpenClaw config.
        Returns stats: {added: [...], removed: [...], updated: [...], source: str}
        """
        from app.services.openclaw_config_reader import get_agent_definitions

        agents_from_config = await get_agent_definitions()
        if agents_from_config is None:
            return {"added": [], "removed": [], "updated": [], "source": "unavailable"}

        # Ensure state is loaded first
        self._load()

        stats: dict[str, Any] = {"added": [], "removed": [], "updated": [], "source": "openclaw_config"}
        config_ids = {a["id"] for a in agents_from_config}

        # Add new / update existing agents
        for config_agent in agents_from_config:
            agent_id = config_agent["id"]
            if agent_id in self._agents:
                # Update config-owned fields, preserve dashboard-owned
                existing = self._agents[agent_id]
                changed = False
                for field in _CONFIG_OWNED_FIELDS:
                    if field in config_agent and existing.get(field) != config_agent[field]:
                        existing[field] = config_agent[field]
                        changed = True
                if changed:
                    stats["updated"].append(agent_id)
            else:
                # New agent from config
                new_agent = {**config_agent, **_idle_defaults()}
                self._agents[agent_id] = new_agent
                stats["added"].append(agent_id)

        # Remove agents no longer in config
        removed_ids = [aid for aid in self._agents if aid not in config_ids]
        for aid in removed_ids:
            del self._agents[aid]
            stats["removed"].append(aid)

        # Save if anything changed
        if stats["added"] or stats["removed"] or stats["updated"]:
            self._save()
            changes = []
            if stats["added"]:
                changes.append(f"added={stats['added']}")
            if stats["removed"]:
                changes.append(f"removed={stats['removed']}")
            if stats["updated"]:
                changes.append(f"updated={stats['updated']}")
            print(f"[agent_repo] Config sync: {', '.join(changes)}")

        return stats

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
        """Sync from config on startup, fallback to seed if needed."""
        stats = await self.sync_from_config()
        if stats["source"] == "unavailable":
            # Config unavailable — just load from state.json or seed
            self._load()
            if not self._agents:
                print("[agent_repo] WARNING: No config source and no state.json. Using empty agent list.")


agent_repo = AgentRepository()
