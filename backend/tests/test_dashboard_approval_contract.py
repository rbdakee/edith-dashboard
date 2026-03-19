from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.domain.models import Task  # noqa: E402
from app.services.task_approval_hook import _build_agent_message  # noqa: E402
from app.services import task_runtime  # noqa: E402


def test_dashboard_approval_contract_contains_required_report_back_fields() -> None:
    task = Task(
        id="tsk_123",
        title="Implement feature",
        runtime_metadata={
            "dashboard_approval": {
                "report_back_session": "agent:main:telegram:direct:123",
                "report_back_channel": "telegram",
                "report_back_chat_id": "123",
                "main_session_id": "ses_main",
                "executor_session_id": "ses_exec",
            }
        },
    )

    message = _build_agent_message(task)

    assert "contract: dashboard.approval.v1" in message
    assert "task_id: tsk_123" in message
    assert "report_back_session: agent:main:telegram:direct:123" in message
    assert "report_back_channel: telegram" in message
    assert "report_back_chat_id: 123" in message
    assert "main_session_id: ses_main" in message
    assert "executor_session_id: ses_exec" in message


def test_apply_execution_outcome_auto_closes_and_persists_correlation_metadata(monkeypatch) -> None:
    task = Task(id="tsk_exec", title="Runtime task", status="in_progress", runtime_metadata={"task_id": "tsk_exec"})

    class FakeRepo:
        async def get(self, task_id: str):
            return task if task_id == task.id else None

        async def update(self, task_id: str, updates: dict):
            data = task.model_dump(mode="json")
            data.update(updates)
            return Task(**data)

    emitted: list[tuple[str, dict]] = []

    async def fake_emit(event_type: str, **kwargs):
        emitted.append((event_type, kwargs))

    async def fake_report_back(**kwargs):
        return None

    monkeypatch.setattr(task_runtime, "task_repo", FakeRepo())
    monkeypatch.setattr(task_runtime, "emit_event", fake_emit)
    monkeypatch.setattr(task_runtime, "trigger_report_back_to_main", fake_report_back)

    updated = asyncio.run(
        task_runtime.apply_execution_outcome(
            task_id="tsk_exec",
            success=True,
            summary="Done",
            main_session_id="ses_main",
            executor_session_id="ses_exec",
            report_back_session="agent:main:telegram:direct:123",
            report_back_channel="telegram",
            report_back_chat_id="123",
        )
    )

    assert updated is not None
    assert updated.status == "done"
    assert updated.sub_status is None
    assert updated.runtime_metadata["main_session_id"] == "ses_main"
    assert updated.runtime_metadata["executor_session_id"] == "ses_exec"
    assert updated.runtime_metadata["report_back_chat_id"] == "123"
    assert emitted and emitted[0][0] == "task.execution_completed"
