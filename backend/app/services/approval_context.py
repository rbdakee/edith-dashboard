from __future__ import annotations

from typing import Any

from app.domain.models import Session
from app.storage.session_repo import session_repo


def _extract_chat_id(session: Session) -> str | None:
    snapshot = session.context_snapshot or {}
    raw_chat_id = snapshot.get("chat_id")
    if isinstance(raw_chat_id, (str, int)):
        value = str(raw_chat_id).strip()
        if value:
            return value

    session_key = session.openclaw_session_id or snapshot.get("session_key")
    if isinstance(session_key, str) and session_key.startswith("agent:main:telegram:direct:"):
        suffix = session_key.split(":")[-1].strip()
        return suffix or None
    return None


def _channel_session_candidates(sessions: list[Session]) -> list[Session]:
    result: list[Session] = []
    for s in sessions:
        snapshot = s.context_snapshot or {}
        if snapshot.get("source_kind") != "channel":
            continue
        channel = snapshot.get("channel")
        if not isinstance(channel, str) or not channel.strip():
            continue
        result.append(s)
    return result


def _resolve_context_from_session(session: Session) -> dict[str, Any] | None:
    snapshot = session.context_snapshot or {}

    report_back_session = (
        snapshot.get("session_key")
        or session.openclaw_session_id
        or snapshot.get("session_id")
    )
    if not isinstance(report_back_session, str) or not report_back_session.strip():
        return None

    report_back_channel = snapshot.get("channel")
    if not isinstance(report_back_channel, str) or not report_back_channel.strip():
        return None

    return {
        "report_back_session": report_back_session,
        "report_back_channel": report_back_channel,
        "report_back_chat_id": _extract_chat_id(session),
        "main_session_id": session.id,
        # executor_session_id becomes known only after delegation/runtime spawn.
        "executor_session_id": None,
    }


async def resolve_report_back_context() -> dict[str, Any] | None:
    """Resolve report-back target from main channel sessions.

    Priority:
    1) newest active main channel session;
    2) newest known main channel session (completed/archived included) as durable fallback.
    """
    active_sessions = await session_repo.list(agent_id="main", status="active", limit=200)
    active_channel_sessions = _channel_session_candidates(active_sessions)
    if active_channel_sessions:
        current_active = max(active_channel_sessions, key=lambda s: s.started_at)
        context = _resolve_context_from_session(current_active)
        if context:
            return context

    # Durable fallback when active session was auto-closed/reconciled before approval.
    all_main_sessions = await session_repo.list(agent_id="main", limit=500)
    all_channel_sessions = _channel_session_candidates(all_main_sessions)
    if not all_channel_sessions:
        return None

    latest_known = max(all_channel_sessions, key=lambda s: s.started_at)
    return _resolve_context_from_session(latest_known)
