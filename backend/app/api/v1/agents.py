from fastapi import APIRouter, HTTPException, Depends

from app.core.deps import get_current_user
from app.domain.models import Agent, AgentUpdate
from app.storage.agent_repo import agent_repo

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/")
async def list_agents(_user: str = Depends(get_current_user)):
    agents = await agent_repo.list()
    return [a.model_dump(mode="json") for a in agents]


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
