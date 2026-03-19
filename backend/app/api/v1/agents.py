from fastapi import APIRouter, HTTPException, Depends

from app.core.deps import get_current_user
from app.domain.models import Agent, AgentUpdate
from app.storage.agent_repo import agent_repo
from app.storage.session_repo import session_repo
from app.services.main_session_presence import find_active_main_telegram_session, build_main_session_context

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/")
async def list_agents(_user: str = Depends(get_current_user)):
    agents = await agent_repo.list()

    # Surface main Telegram direct session as presence on E.D.I.T.H. (main)
    # while Sessions API hides that single row.
    all_sessions = await session_repo.list(limit=1000)
    active_main_session = find_active_main_telegram_session(all_sessions)

    payload = []
    for agent in agents:
        row = agent.model_dump(mode="json")
        if agent.id == "main" and active_main_session is not None:
            row["status"] = "active"
            row["current_session_id"] = active_main_session.openclaw_session_id or active_main_session.id
            row["current_session_context"] = build_main_session_context(active_main_session)
            row["last_active_at"] = active_main_session.started_at.isoformat() if hasattr(active_main_session.started_at, "isoformat") else active_main_session.started_at
        payload.append(row)

    return payload


@router.get("/{agent_id}")
async def get_agent(agent_id: str, _user: str = Depends(get_current_user)):
    agent = await agent_repo.get(agent_id)
    if agent is None:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return agent.model_dump(mode="json")


@router.patch("/{agent_id}")
async def patch_agent(
    agent_id: str,
    data: AgentUpdate,
    _user: str = Depends(get_current_user),
):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")
    updated = await agent_repo.update(agent_id, updates)
    if updated is None:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return updated.model_dump(mode="json")
