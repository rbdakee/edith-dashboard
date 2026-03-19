"""
Gateway poller: polls OpenClaw gateway at :18789 every 10s for agent/session state.
"""
import asyncio
from datetime import datetime, timezone

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

_scheduler: AsyncIOScheduler | None = None
_event_bus = None
_gateway_url: str = ""
_gateway_token: str = ""


async def _poll_gateway():
    if not _gateway_url or not _gateway_token:
        return

    headers = {
        "Authorization": f"Bearer {_gateway_token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Poll agents
            try:
                resp = await client.get(f"{_gateway_url}/api/agents", headers=headers)
                if resp.status_code == 200:
                    agents = resp.json()
                    if _event_bus:
                        await _event_bus.publish({
                            "type": "agent.status_changed",
                            "source": "gateway",
                            "title": "Agent state polled",
                            "data": {"agents": agents},
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
            except Exception:
                pass

            # Poll active sessions
            try:
                resp = await client.get(f"{_gateway_url}/api/sessions", headers=headers)
                if resp.status_code == 200:
                    sessions = resp.json()
                    if _event_bus and sessions:
                        await _event_bus.publish({
                            "type": "session.started",
                            "source": "gateway",
                            "title": f"{len(sessions)} active session(s)",
                            "data": {"sessions": sessions},
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
            except Exception:
                pass

    except Exception as e:
        pass  # Gateway might be offline; that's fine


def start_gateway_poller(event_bus, gateway_url: str, gateway_token: str):
    global _scheduler, _event_bus, _gateway_url, _gateway_token
    _event_bus = event_bus
    _gateway_url = gateway_url
    _gateway_token = gateway_token

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_poll_gateway, "interval", seconds=10, id="gateway_poll")
    try:
        _scheduler.start()
    except Exception as e:
        print(f"[gateway_poller] Could not start scheduler: {e}")


def stop_gateway_poller():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
