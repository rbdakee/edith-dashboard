from __future__ import annotations

from typing import Any

from app.domain.models import Session

_MAIN_TELEGRAM_DIRECT_PREFIX = "agent:main:telegram:direct:"


def is_current_main_telegram_session(session: Session) -> bool:
    """True only for main agent's direct Telegram session representation."""
    if session.agent_id != "main":
        return False

    openclaw_id = (session.openclaw_session_id or "").strip()
    if not openclaw_id.startswith(_MAIN_TELEGRAM_DIRECT_PREFIX):
        return False

    source_kind = str(session.context_snapshot.get("source_kind", "")).strip()
    channel = str(session.context_snapshot.get("channel", "")).strip()
    return source_kind == "channel" and channel == "telegram"


def build_main_session_context(session: Session) -> dict[str, Any]:
    """Compact context used by Agents page for current E.D.I.T.H. main presence."""
    snapshot = session.context_snapshot or {}
    return {
        "source_kind": snapshot.get("source_kind"),
        "channel": snapshot.get("channel"),
        "session_key": snapshot.get("session_key"),
        "session_id": snapshot.get("session_id"),
    }


def find_active_main_telegram_session(sessions: list[Session]) -> Session | None:
    """Return the currently active main Telegram direct session if present."""
    matches = [
        s for s in sessions
        if s.status == "active" and is_current_main_telegram_session(s)
    ]
    if not matches:
        return None
    # Keep deterministic: newest active session wins.
    return max(matches, key=lambda s: s.started_at)
