"""
Reads agent definitions from OpenClaw config (openclaw.json).

Tries Gateway API first (future-proof), falls back to filesystem read.
Extracts: id, name, model, skills from agents.list.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from app.config import settings


async def fetch_agents_from_gateway() -> list[dict[str, Any]] | None:
    """Try fetching agent list from Gateway API. Returns None if unavailable."""
    url = settings.openclaw_gateway_url.rstrip("/")
    token = settings.openclaw_gateway_token
    if not url or not token:
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{url}/api/config",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return _extract_agents(data)
    except Exception:
        pass
    return None


def read_agents_from_file() -> list[dict[str, Any]] | None:
    """Read agent list from openclaw.json on filesystem."""
    config_path = Path(settings.openclaw_dir) / "openclaw.json"
    if not config_path.exists():
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _extract_agents(data)
    except Exception as e:
        print(f"[openclaw_config_reader] Error reading {config_path}: {e}")
        return None


def _extract_agents(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract agent definitions from openclaw config structure."""
    agents_list = config.get("agents", {}).get("list", [])
    result = []
    for agent in agents_list:
        agent_id = agent.get("id")
        if not agent_id:
            continue
        result.append({
            "id": agent_id,
            "name": agent.get("name", agent_id),
            "model": agent.get("model", ""),
            "skills": agent.get("skills", []),
        })
    return result


async def get_agent_definitions() -> list[dict[str, Any]] | None:
    """
    Get agent definitions: Gateway API first, then filesystem fallback.
    Returns None if both fail.
    """
    # Try Gateway API (future-proof for when /api/config exists)
    agents = await fetch_agents_from_gateway()
    if agents is not None:
        return agents

    # Fallback: read from filesystem
    agents = read_agents_from_file()
    if agents is not None:
        return agents

    return None
