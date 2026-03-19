from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.domain.models import Task  # noqa: E402
from app.services import task_service  # noqa: E402


class FakeRepo:
    def __init__(self, task: Task):
        self.task = task

    async def get(self, task_id: str):
        return self.task if task_id == self.task.id else None

    async def update(self, task_id: str, updates: dict):
        data = self.task.model_dump(mode="json")
        data.update(updates)
        self.task = Task(**data)
        return self.task


async def _noop_emit(*_args, **_kwargs):
    return None


def _noop_schedule(_task):
    return None


def test_approve_task_merges_context_sources_with_payload_priority(monkeypatch) -> None:
    task = Task(
        id="tsk_ctx_merge",
        title="Merge context",
        status="planned",
        runtime_metadata={
            "dashboard_approval": {
                "report_back_channel": "telegram",
                "main_session_id": "ses_existing",
            }
        },
    )

    repo = FakeRepo(task)

    async def fake_fallback_context():
        return {
            "report_back_session": "agent:main:telegram:direct:893220231",
            "report_back_chat_id": "893220231",
            "main_session_id": "ses_fallback",
        }

    monkeypatch.setattr(task_service, "task_repo", repo)
    monkeypatch.setattr(task_service, "resolve_report_back_context", fake_fallback_context)
    monkeypatch.setattr(task_service, "emit_event", _noop_emit)
    monkeypatch.setattr(task_service, "schedule_approval_hook", _noop_schedule)

    updated = asyncio.run(
        task_service.approve_task(
            "tsk_ctx_merge",
            report_back_context={"main_session_id": "ses_payload"},
        )
    )

    assert updated is not None
    approval = updated.runtime_metadata["dashboard_approval"]
    assert approval["report_back_channel"] == "telegram"  # from existing
    assert approval["report_back_session"] == "agent:main:telegram:direct:893220231"  # from fallback
    assert approval["report_back_chat_id"] == "893220231"  # from fallback
    assert approval["main_session_id"] == "ses_payload"  # payload wins


def test_approve_task_missing_required_context_has_detailed_error(monkeypatch) -> None:
    task = Task(id="tsk_ctx_error", title="Missing context", status="planned")
    repo = FakeRepo(task)

    async def fake_empty_context():
        return {}

    monkeypatch.setattr(task_service, "task_repo", repo)
    monkeypatch.setattr(task_service, "resolve_report_back_context", fake_empty_context)

    try:
        asyncio.run(task_service.approve_task("tsk_ctx_error", report_back_context={"main_session_id": "ses_only"}))
    except ValueError as exc:
        msg = str(exc)
        assert "missing=['report_back_session', 'report_back_channel']" in msg
        assert "provided=['main_session_id']" in msg
    else:
        raise AssertionError("Expected ValueError for missing report-back context")
