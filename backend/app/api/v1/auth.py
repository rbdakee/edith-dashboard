from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
from pathlib import Path
import secrets

from app.config import settings
from app.core.auth import hash_password, verify_password, create_access_token, verify_jwt
from app.storage.json_store import read_json, write_json

router = APIRouter(prefix="/auth", tags=["auth"])


class SetupRequest(BaseModel):
    password: str


class LoginRequest(BaseModel):
    password: str


def _auth_config_path() -> Path:
    return Path(settings.data_dir) / "config" / "auth.json"


@router.post("/setup")
async def setup(req: SetupRequest):
    """First-time setup: set password and generate secrets."""
    config_path = _auth_config_path()
    if config_path.exists():
        raise HTTPException(400, "Already configured. Use /auth/login.")
    config = {
        "password_hash": hash_password(req.password),
        "jwt_secret": secrets.token_hex(32),
        "ingest_api_key": secrets.token_hex(24),
    }
    write_json(config_path, config)
    return {"ok": True, "ingest_api_key": config["ingest_api_key"]}


@router.post("/login")
async def login(req: LoginRequest, response: Response):
    """Login and receive JWT cookie."""
    config = read_json(_auth_config_path())
    if not config:
        raise HTTPException(400, "Not configured. Use /auth/setup first.")
    if not verify_password(req.password, config["password_hash"]):
        raise HTTPException(401, "Invalid password")
    token = create_access_token(config["jwt_secret"])
    response.set_cookie(
        key="access_token", value=token,
        httponly=True, samesite="strict", max_age=86400,
    )
    return {"ok": True}


@router.get("/me")
async def me(request: Request):
    """Check if current session is authenticated."""
    token = request.cookies.get("access_token", "")
    config = read_json(_auth_config_path())
    if not config or not verify_jwt(token, config.get("jwt_secret", "")):
        raise HTTPException(401, "Not authenticated")
    return {"ok": True, "user": "doszhan"}


@router.get("/status")
async def auth_status():
    """Check if setup has been completed."""
    return {"configured": _auth_config_path().exists()}


@router.get("/ws-token")
async def ws_token(request: Request):
    """Return JWT for WebSocket auth — reads from httpOnly cookie, returns in body."""
    token = request.cookies.get("access_token", "")
    config = read_json(_auth_config_path())
    if not config or not verify_jwt(token, config.get("jwt_secret", "")):
        raise HTTPException(401, "Not authenticated")
    return {"token": token}


@router.post("/logout")
async def logout(response: Response):
    """Clear auth cookie."""
    response.delete_cookie("access_token")
    return {"ok": True}
