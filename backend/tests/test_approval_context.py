from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.domain.models import Session  # noqa: E402
from app.services import approval_context  # noqa: E402


class FakeSessionRepo:
    def __init__(self, active: list[Session], all_rows: list[Session]):
        self._active = active
        self._all = all_rows

    async def list(self, agent_id: str | None = None, status: str | None = None, limit: int = 50):
        rows = self._active if status == "active" else self._all
        if agent_id:
            rows = [row for row in rows if row.agent_id == agent_id]
        return rows[:limit]


def _session(*, sid: str, status: str, started_at: datetime, session_key: str, channel: str = "telegram") -> Session:
    return Session(
        id=sid,
        agent_id="main",
        status=status,
        started_at=started_at,
        openclaw_session_id=session_key,
        context_snapshot={
            "source_kind": "channel",
            "channel": channel,
            "session_key": session_key,
        },
    )


def test_resolve_report_back_context_uses_active_main_channel_session(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    older = _session(
        sid="ses_old_active",
        status="active",
        started_at=now - timedelta(minutes=10),
        session_key="agent:main:telegram:direct:111",
    )
    newer = _session(
        sid="ses_new_active",
        status="active",
        started_at=now - timedelta(minutes=2),
        session_key="agent:main:telegram:direct:222",
    )
    repo = FakeSessionRepo(active=[older, newer], all_rows=[older, newer])
    monkeypatch.setattr(approval_context, "session_repo", repo)

    context = asyncio.run(approval_context.resolve_report_back_context())

    assert context is not None
    assert context["report_back_session"] == "agent:main:telegram:direct:222"
    assert context["report_back_channel"] == "telegram"
    assert context["report_back_chat_id"] == "222"
    assert context["main_session_id"] == "ses_new_active"


def test_resolve_report_back_context_falls_back_to_latest_completed_main_session(monkeypatch) -> None:
    now = datetime.now(timezone.utc)
    completed_old = _session(
        sid="ses_completed_old",
        status="completed",
        started_at=now - timedelta(hours=2),
        session_key="agent:main:telegram:direct:333",
    )
    completed_latest = _session(
        sid="ses_completed_latest",
        status="completed",
        started_at=now - timedelta(minutes=30),
        session_key="agent:main:telegram:direct:893220231",
    )
    repo = FakeSessionRepo(active=[], all_rows=[completed_old, completed_latest])
    monkeypatch.setattr(approval_context, "session_repo", repo)

    context = asyncio.run(approval_context.resolve_report_back_context())

    assert context is not None
    assert context["report_back_session"] == "agent:main:telegram:direct:893220231"
    assert context["report_back_channel"] == "telegram"
    assert context["report_back_chat_id"] == "893220231"
    assert context["main_session_id"] == "ses_completed_latest"
