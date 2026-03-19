from datetime import datetime, timezone
from typing import Any

from app.domain.models import Agent
from app.domain.enums import AgentStatus, EventSource
from app.storage.agent_repo import agent_repo
from app.services.event_service import emit_event


async def update_agent_status(agent_id: str, status: AgentStatus, task_id: str | None = None) -> Agent | None:
    updates: dict[str, Any] = {
        "status": status,
        "last_active_at": datetime.now(timezone.utc).isoformat(),
    }
    if task_id is not None:
        updates["current_task_id"] = task_id

    agent = await agent_repo.update(agent_id, updates)
    if agent:
        await emit_event(
            "agent.status_changed",
            title=f"Agent {agent_id} status: {status}",
            agent_id=agent_id,
            source=EventSource.gateway,
            data={"status": status, "task_id": task_id},
        )
    return agent
