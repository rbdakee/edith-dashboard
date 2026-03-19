from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.domain.models import Session  # noqa: E402
from app.services.openclaw_session_truth import reconcile_sessions_with_openclaw_truth  # noqa: E402
from app.services.session_metadata import _load_openclaw_session_aliases_cached  # noqa: E402
from app.storage.session_repo import session_repo  # noqa: E402


def _reset_session_repo_state() -> None:
    session_repo._index = {}
    session_repo._cache = {}
    session_repo._loaded = False


def test_find_by_openclaw_refs_matches_aliases(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    openclaw_dir = tmp_path / "openclaw"
    sessions_dir = openclaw_dir / "agents" / "edith-dev" / "sessions"
    sessions_dir.mkdir(parents=True)
    (sessions_dir / "sessions.json").write_text(
        json.dumps(
            {
                "agent:edith-dev:subagent:dup": {
                    "sessionId": "uuid-123",
                    "spawnDepth": 1,
                    "spawnedBy": "agent:main:telegram:direct:893220231",
                }
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(settings, "data_dir", str(data_dir))
    monkeypatch.setattr(settings, "openclaw_dir", str(openclaw_dir))
    _load_openclaw_session_aliases_cached.cache_clear()
    _reset_session_repo_state()

    row = Session(
        id="ses_alias",
        agent_id="edith-dev",
        openclaw_session_id="uuid-123",
        status="active",
        started_at=datetime.now(timezone.utc),
        context_snapshot={
            "source": "openclaw",
            "session_key": "agent:edith-dev:subagent:dup",
            "session_id": "uuid-123",
            "source_kind": "agent",
            "channel": "openclaw",
        },
    )
    asyncio.run(session_repo.create(row))

    found = asyncio.run(session_repo.find_by_openclaw_refs("agent:edith-dev:subagent:dup"))
    assert found is not None
    assert found.id == "ses_alias"


def test_reconcile_closes_stale_and_duplicate_active_rows(monkeypatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    openclaw_dir = tmp_path / "openclaw"
    sessions_dir = openclaw_dir / "agents" / "edith-dev" / "sessions"
    sessions_dir.mkdir(parents=True)

    session_key = "agent:edith-dev:subagent:dup"
    session_id = "uuid-live"
    (sessions_dir / "sessions.json").write_text(
        json.dumps(
            {
                session_key: {
                    "sessionId": session_id,
                    "spawnDepth": 1,
                    "spawnedBy": "agent:main:telegram:direct:893220231",
                }
            }
        ),
        encoding="utf-8",
    )
    (sessions_dir / f"{session_id}.jsonl.lock").write_text("", encoding="utf-8")

    monkeypatch.setattr(settings, "data_dir", str(data_dir))
    monkeypatch.setattr(settings, "openclaw_dir", str(openclaw_dir))
    _load_openclaw_session_aliases_cached.cache_clear()
    _reset_session_repo_state()

    now = datetime.now(timezone.utc)
    older_duplicate = Session(
        id="ses_old_dup",
        agent_id="edith-dev",
        openclaw_session_id=session_key,
        status="active",
        started_at=now - timedelta(minutes=5),
        context_snapshot={
            "source": "openclaw",
            "session_key": session_key,
            "session_id": session_id,
            "source_kind": "agent",
            "channel": "openclaw",
        },
    )
    newest_live = Session(
        id="ses_live",
        agent_id="edith-dev",
        openclaw_session_id=session_id,
        status="active",
        started_at=now - timedelta(minutes=1),
        context_snapshot={
            "source": "openclaw",
            "session_key": session_key,
            "session_id": session_id,
            "source_kind": "agent",
            "channel": "openclaw",
        },
    )
    stale_missing = Session(
        id="ses_stale",
        agent_id="edith-dev",
        openclaw_session_id="uuid-missing",
        status="active",
        started_at=now - timedelta(minutes=10),
        context_snapshot={
            "source": "openclaw",
            "session_key": "agent:edith-dev:subagent:missing",
            "session_id": "uuid-missing",
            "source_kind": "agent",
            "channel": "openclaw",
        },
    )

    for row in (older_duplicate, newest_live, stale_missing):
        asyncio.run(session_repo.create(row))

    stats = asyncio.run(reconcile_sessions_with_openclaw_truth(str(openclaw_dir), stale_seconds=0))

    assert stats["active_rows_seen"] == 3
    assert stats["closed"] == 2
    assert stats["kept"] == 1

    refreshed_live = asyncio.run(session_repo.get("ses_live"))
    refreshed_old_dup = asyncio.run(session_repo.get("ses_old_dup"))
    refreshed_stale = asyncio.run(session_repo.get("ses_stale"))

    assert refreshed_live is not None
    assert refreshed_live.status == "active"
    assert refreshed_live.ended_at is None

    assert refreshed_old_dup is not None
    assert refreshed_old_dup.status == "completed"
    assert refreshed_old_dup.ended_at is not None
    assert refreshed_old_dup.context_snapshot.get("terminal_reason") == "superseded_duplicate_active_row"

    assert refreshed_stale is not None
    assert refreshed_stale.status == "completed"
    assert refreshed_stale.ended_at is not None
    assert refreshed_stale.context_snapshot.get("terminal_reason") == "missing_from_openclaw_truth"
