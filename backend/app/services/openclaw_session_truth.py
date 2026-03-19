from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.storage.session_repo import session_repo


def _extract_session_id_from_lock(lock_path: Path) -> str | None:
    name = lock_path.name
    if not name.endswith('.jsonl.lock'):
        return None
    return name[: -len('.jsonl.lock')]


def _iter_active_lock_session_ids(openclaw_dir: str) -> set[str]:
    root = Path(openclaw_dir) / 'agents'
    if not root.exists():
        return set()

    active_ids: set[str] = set()
    for lock_path in root.glob('*/sessions/*.jsonl.lock'):
        sid = _extract_session_id_from_lock(lock_path)
        if sid:
            active_ids.add(sid)
    return active_ids


def _load_session_key_to_id_map(openclaw_dir: str) -> dict[str, str]:
    root = Path(openclaw_dir) / 'agents'
    if not root.exists():
        return {}

    result: dict[str, str] = {}
    for idx_path in root.glob('*/sessions/sessions.json'):
        try:
            raw = json.loads(idx_path.read_text(encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(raw, dict):
            continue

        for session_key, payload in raw.items():
            if not isinstance(payload, dict):
                continue
            sid = payload.get('sessionId')
            if isinstance(session_key, str) and isinstance(sid, str) and sid:
                result[session_key] = sid
    return result


def active_openclaw_identifiers(openclaw_dir: str) -> set[str]:
    """
    Returns active identifiers in both formats used by edith-ops sessions:
      - raw OpenClaw session UUID (jsonl/.lock stem)
      - OpenClaw sessionKey (agent:...)
    A sessionKey is considered active iff its current sessionId has an active .lock file.
    """
    active_ids = _iter_active_lock_session_ids(openclaw_dir)
    if not active_ids:
        return set()

    key_to_id = _load_session_key_to_id_map(openclaw_dir)
    active_identifiers = set(active_ids)
    for session_key, sid in key_to_id.items():
        if sid in active_ids:
            active_identifiers.add(session_key)
    return active_identifiers


async def reconcile_sessions_with_openclaw_truth(
    openclaw_dir: str,
    stale_seconds: int = 30,
) -> dict[str, int]:
    """
    Close dashboard-active sessions that are not active in real OpenClaw locks map.
    Uses a small grace period to avoid transient lock races.
    """
    active_identifiers = active_openclaw_identifiers(openclaw_dir)
    active_rows = await session_repo.list(status='active', limit=1000)

    now = datetime.now(timezone.utc)
    closed = 0
    kept = 0

    for row in active_rows:
        oid = (row.openclaw_session_id or '').strip()
        if oid and oid in active_identifiers:
            kept += 1
            continue

        started_at = row.started_at
        age_seconds = 0.0
        if isinstance(started_at, datetime):
            base = started_at if started_at.tzinfo else started_at.replace(tzinfo=timezone.utc)
            age_seconds = (now - base).total_seconds()

        if age_seconds < stale_seconds:
            kept += 1
            continue

        await session_repo.update(
            row.id,
            {
                'status': 'completed',
                'ended_at': now.isoformat(),
                'context_snapshot': {
                    **(row.context_snapshot or {}),
                    'auto_closed_by': 'openclaw_truth_reconcile',
                },
            },
        )
        closed += 1

    return {
        'active_truth_identifiers': len(active_identifiers),
        'active_rows_seen': len(active_rows),
        'closed': closed,
        'kept': kept,
    }
