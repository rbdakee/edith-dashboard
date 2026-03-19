from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio

from app.core.event_bus import event_bus
from app.core.auth import verify_jwt
from app.storage.json_store import read_json
from app.config import settings
from pathlib import Path

ws_router = APIRouter()


def _get_jwt_secret() -> str:
    config = read_json(Path(settings.data_dir) / "config" / "auth.json")
    return config.get("jwt_secret", "") if config else ""


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        try:
            self.active.remove(ws)
        except ValueError:
            pass

    async def broadcast(self, message: dict):
        data = json.dumps(message, default=str)
        for ws in list(self.active):
            try:
                await ws.send_text(data)
            except Exception:
                pass


manager = ConnectionManager()


@ws_router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)

    # First message must be auth token
    try:
        auth_msg = await ws.receive_text()
        auth_data = json.loads(auth_msg)
        token = auth_data.get("token", "")
        secret = _get_jwt_secret()
        if not verify_jwt(token, secret):
            await ws.close(code=4001, reason="Unauthorized")
            manager.disconnect(ws)
            return
    except Exception:
        await ws.close(code=4001)
        manager.disconnect(ws)
        return

    # Subscribe to event bus
    queue = event_bus.subscribe()

    async def send_events():
        try:
            while True:
                event = await queue.get()
                await ws.send_text(json.dumps({"type": "event", "payload": event}, default=str))
        except Exception:
            pass

    send_task = asyncio.create_task(send_events())

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                await handle_client_message(msg)
            except Exception:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        send_task.cancel()
        event_bus.unsubscribe(queue)
        manager.disconnect(ws)


async def handle_client_message(msg: dict):
    """Handle messages from the frontend (comments, approvals)."""
    from app.ws.handlers import dispatch_client_message
    await dispatch_client_message(msg)
