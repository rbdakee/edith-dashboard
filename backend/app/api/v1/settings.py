from fastapi import APIRouter, Depends, HTTPException  # noqa: F401
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.storage.config_repo import config_repo
from app.services.notion_sync import run_sync_job

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    notion_sync_enabled: bool | None = None
    notion_sync_interval_seconds: int | None = None
    gateway_poll_interval_seconds: int | None = None
    notifications_enabled: bool | None = None
    theme: str | None = None


@router.get("/")
async def get_settings(_user: str = Depends(get_current_user)):
    app_settings = await config_repo.get_settings()
    return app_settings.model_dump(mode="json")


@router.patch("/")
async def update_settings(
    data: SettingsUpdate,
    _user: str = Depends(get_current_user),
):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = await config_repo.update_settings(updates)
    return updated.model_dump(mode="json")


@router.post("/sync")
async def trigger_sync(_user: str = Depends(get_current_user)):
    """Trigger manual Notion sync."""
    try:
        await run_sync_job()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
