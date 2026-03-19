from fastapi import HTTPException, Request
from pathlib import Path

from app.core.auth import verify_jwt
from app.storage.json_store import read_json
from app.config import settings


def _get_auth_config() -> dict | None:
    return read_json(Path(settings.data_dir) / "config" / "auth.json")


def get_current_user(request: Request) -> str:
    """FastAPI dependency: verify JWT from cookie, return username."""
    token = request.cookies.get("access_token", "")
    config = _get_auth_config()
    if not config:
        raise HTTPException(status_code=401, detail="Not configured")
    if not verify_jwt(token, config.get("jwt_secret", "")):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return "doszhan"
