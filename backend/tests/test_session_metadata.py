from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.domain.models import Session  # noqa: E402
from app.services.main_session_presence import is_current_main_telegram_session  # noqa: E402
from app.services.session_metadata import classify_session_source, normalize_session_snapshot  # noqa: E402


def test_classify_subagent_ignores_inherited_parent_telegram_channel() -> None:
    source_kind, channel = classify_session_source(
        source="openclaw",
        session_key="agent:edith-dev:subagent:f45024b6-4db4-4273-b8d7-ed48da39bd9d",
        meta={
            "delivery_context": {"channel": "telegram"},
            "last_channel": "telegram",
            "spawn_depth": 1,
            "spawned_by": "agent:main:telegram:direct:893220231",
        },
    )

    assert source_kind == "agent"
    assert channel == "openclaw"



def test_classify_main_telegram_direct_remains_channel_session() -> None:
    source_kind, channel = classify_session_source(
        source="openclaw",
        session_key="agent:main:telegram:direct:893220231",
        meta={
            "delivery_context": {"channel": "telegram"},
            "last_channel": "telegram",
        },
    )

    assert source_kind == "channel"
    assert channel == "telegram"



def test_normalize_session_snapshot_reclassifies_stored_subagent_row() -> None:
    normalized = normalize_session_snapshot(
        openclaw_session_ref="agent:edith-dev:subagent:abc123",
        snapshot={
            "source": "openclaw",
            "source_kind": "channel",
            "channel": "telegram",
            "session_key": "agent:edith-dev:subagent:abc123",
        },
    )

    assert normalized["source"] == "openclaw"
    assert normalized["source_kind"] == "agent"
    assert normalized["channel"] == "openclaw"
    assert normalized["session_key"] == "agent:edith-dev:subagent:abc123"



def test_main_presence_rule_does_not_match_subagent_session() -> None:
    session = Session(
        agent_id="edith-dev",
        openclaw_session_id="agent:edith-dev:subagent:abc123",
        context_snapshot={
            "source": "openclaw",
            "source_kind": "agent",
            "channel": "openclaw",
            "session_key": "agent:edith-dev:subagent:abc123",
        },
    )

    assert is_current_main_telegram_session(session) is False
