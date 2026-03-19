"""
Background poller for periodic OpenClaw truth reconciliation.

Historically this module polled guessed gateway HTTP endpoints (/api/agents, /api/sessions),
which may not exist and produced stale state. Now it reconciles sessions directly from
local OpenClaw session lock/files truth.
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

_scheduler: AsyncIOScheduler | None = None
_openclaw_dir: str = ""


async def _poll_gateway():
    if not _openclaw_dir:
        return

    from app.services.openclaw_session_truth import reconcile_sessions_with_openclaw_truth

    try:
        stats = await reconcile_sessions_with_openclaw_truth(
            openclaw_dir=_openclaw_dir,
            stale_seconds=30,
        )
        if stats.get("closed"):
            print(f"[gateway_poller] reconciled sessions: {stats}")
    except Exception as e:
        print(f"[gateway_poller] reconcile error: {e}")

    # Periodic agent config sync
    await _sync_agents()


async def _sync_agents():
    """Sync agent definitions from OpenClaw config."""
    try:
        from app.storage.agent_repo import agent_repo
        stats = await agent_repo.sync_from_config()
        # Only log if something actually changed
        if stats.get("added") or stats.get("removed") or stats.get("updated"):
            print(f"[gateway_poller] agent sync: {stats}")
    except Exception as e:
        print(f"[gateway_poller] agent sync error: {e}")


def start_gateway_poller(event_bus, gateway_url: str, gateway_token: str, openclaw_dir: str):
    # event_bus/gateway_url/gateway_token kept in signature for backward compatibility
    global _scheduler, _openclaw_dir
    _openclaw_dir = openclaw_dir

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
