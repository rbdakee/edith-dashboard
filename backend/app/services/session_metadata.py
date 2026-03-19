from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings


@lru_cache(maxsize=8)
def _load_openclaw_session_aliases_cached(openclaw_dir: str) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    alias_to_canonical: dict[str, str] = {}
    meta_by_canonical: dict[str, dict[str, Any]] = {}

    if not openclaw_dir:
        return alias_to_canonical, meta_by_canonical

    agents_root = Path(openclaw_dir) / "agents"
    if not agents_root.exists():
        return alias_to_canonical, meta_by_canonical

    for idx_path in agents_root.glob("*/sessions/sessions.json"):
        try:
            raw = json.loads(idx_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(raw, dict):
            continue

        for session_key, payload in raw.items():
            if not isinstance(session_key, str) or not isinstance(payload, dict):
                continue

            session_id = payload.get("sessionId")
            canonical = session_key
            alias_to_canonical[session_key] = canonical
            if isinstance(session_id, str) and session_id:
                alias_to_canonical[session_id] = canonical

            meta_by_canonical[canonical] = {
                "session_key": session_key,
                "session_id": session_id if isinstance(session_id, str) else None,
                "origin": payload.get("origin") if isinstance(payload.get("origin"), dict) else {},
                "delivery_context": payload.get("deliveryContext") if isinstance(payload.get("deliveryContext"), dict) else {},
                "last_channel": payload.get("lastChannel"),
                "channel": payload.get("channel"),
                "spawn_depth": payload.get("spawnDepth"),
                "subagent_role": payload.get("subagentRole"),
                "spawned_by": payload.get("spawnedBy"),
            }

    return alias_to_canonical, meta_by_canonical


def load_openclaw_session_aliases(openclaw_dir: str | None = None) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    return _load_openclaw_session_aliases_cached((openclaw_dir or settings.openclaw_dir or "").strip())


def resolve_session_identity(session_ref: str | None, openclaw_dir: str | None = None) -> tuple[str | None, dict[str, Any]]:
    if not isinstance(session_ref, str) or not session_ref.strip():
        return None, {}

    alias_to_canonical, meta_by_canonical = load_openclaw_session_aliases(openclaw_dir)
    canonical = alias_to_canonical.get(session_ref, session_ref)
    return canonical, meta_by_canonical.get(canonical, {})


def classify_session_source(source: str | None, session_key: str | None, meta: dict[str, Any] | None) -> tuple[str, str | None]:
    """Return canonical (source_kind, channel) for dashboard sessions."""
    meta = meta or {}
    source = source or ""

    origin = meta.get("origin") if isinstance(meta.get("origin"), dict) else {}
    delivery_context = meta.get("delivery_context") if isinstance(meta.get("delivery_context"), dict) else {}

    key_parts = session_key.split(":") if isinstance(session_key, str) else []
    key_surface = key_parts[2] if len(key_parts) >= 3 else None

    is_subagent = (
        key_surface == "subagent"
        or meta.get("spawn_depth") is not None
        or isinstance(meta.get("subagent_role"), str)
        or isinstance(meta.get("spawned_by"), str)
    )
    if is_subagent:
        return "agent", "openclaw"

    channel = None
    if isinstance(delivery_context.get("channel"), str):
        channel = delivery_context.get("channel")
    elif isinstance(meta.get("last_channel"), str):
        channel = meta.get("last_channel")
    elif isinstance(meta.get("channel"), str):
        channel = meta.get("channel")
    elif isinstance(origin.get("provider"), str):
        channel = origin.get("provider")
    elif source and not source.startswith("gateway:"):
        channel = source

    if not channel and isinstance(key_surface, str):
        channel = key_surface

    external_channels = {"telegram", "discord", "slack", "webchat", "tui", "cli", "chrome-relay"}
    if (channel in external_channels) or (key_surface in external_channels):
        return "channel", channel

    if isinstance(source, str) and source.startswith("gateway:"):
        return "internal", channel

    return "agent", channel


def normalize_session_snapshot(
    *,
    openclaw_session_ref: str | None,
    snapshot: dict[str, Any] | None,
    openclaw_dir: str | None = None,
) -> dict[str, Any]:
    current = dict(snapshot or {})

    ref_candidates = [
        current.get("session_key"),
        current.get("session_id"),
        openclaw_session_ref,
    ]
    ref = next((value for value in ref_candidates if isinstance(value, str) and value.strip()), None)

    canonical, meta = resolve_session_identity(ref, openclaw_dir=openclaw_dir)
    resolved_session_key = meta.get("session_key") if isinstance(meta.get("session_key"), str) else None
    resolved_session_id = meta.get("session_id") if isinstance(meta.get("session_id"), str) else None

    if not resolved_session_key and isinstance(current.get("session_key"), str):
        resolved_session_key = current.get("session_key")
    if not resolved_session_id and isinstance(current.get("session_id"), str):
        resolved_session_id = current.get("session_id")

    source = current.get("source") if isinstance(current.get("source"), str) else None
    source_kind, channel = classify_session_source(source=source, session_key=resolved_session_key or canonical, meta=meta)

    normalized = dict(current)
    if source is not None:
        normalized["source"] = source
    if resolved_session_key:
        normalized["session_key"] = resolved_session_key
    elif isinstance(canonical, str) and canonical.startswith("agent:"):
        normalized["session_key"] = canonical
    if resolved_session_id:
        normalized["session_id"] = resolved_session_id
    normalized["source_kind"] = source_kind
    if channel is not None:
        normalized["channel"] = channel
    else:
        normalized.pop("channel", None)

    return normalized
