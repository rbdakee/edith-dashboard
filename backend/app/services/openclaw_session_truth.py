from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from app.storage.session_repo import session_repo
from app.services.session_metadata import resolve_session_identity


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


def _row_identity_candidates(row) -> set[str]:
    snapshot = row.context_snapshot or {}
    refs = {
        value.strip()
        for value in (
            row.openclaw_session_id,
            snapshot.get('session_key'),
            snapshot.get('session_id'),
        )
        if isinstance(value, str) and value.strip()
    }
    canonical_refs = {
        canonical.strip()
        for canonical, _meta in (resolve_session_identity(ref) for ref in refs)
        if isinstance(canonical, str) and canonical and canonical.strip()
    }
    return refs | canonical_refs


def _preferred_row_identity(row) -> str | None:
    snapshot = row.context_snapshot or {}
    for candidate in (
        snapshot.get('session_key'),
        row.openclaw_session_id,
        snapshot.get('session_id'),
    ):
        if isinstance(candidate, str) and candidate.strip():
            canonical, _meta = resolve_session_identity(candidate)
            if isinstance(canonical, str) and canonical.strip():
                return canonical.strip()
            return candidate.strip()
    return None


def _row_age_seconds(row, now: datetime) -> float:
    started_at = row.started_at
    if not isinstance(started_at, datetime):
        return 0.0
    base = started_at if started_at.tzinfo else started_at.replace(tzinfo=timezone.utc)
    return max(0.0, (now - base).total_seconds())


async def _close_rows(rows: Iterable, now: datetime, reason: str) -> int:
    count = 0
    for row in rows:
        await session_repo.update(
            row.id,
            {
                'status': 'completed',
                'ended_at': now.isoformat(),
                'context_snapshot': {
                    **(row.context_snapshot or {}),
                    'auto_closed_by': 'openclaw_truth_reconcile',
                    'terminal_reason': reason,
                },
            },
        )
        count += 1
    return count


async def reconcile_sessions_with_openclaw_truth(
    openclaw_dir: str,
    stale_seconds: int = 30,
) -> dict[str, int]:
    """
    Close dashboard-active sessions that are not active in real OpenClaw locks map.
    Also collapses duplicate active rows that point at the same live OpenClaw session,
    keeping only the newest dashboard row as the active representative.
    """
    active_identifiers = active_openclaw_identifiers(openclaw_dir)
    active_rows = await session_repo.list(status='active', limit=1000)

    now = datetime.now(timezone.utc)
    active_groups: dict[str, list] = defaultdict(list)
    rows_to_close = []
    closed = 0
    kept = 0

    for row in active_rows:
        row_refs = _row_identity_candidates(row)
        is_live = bool(row_refs & active_identifiers)
        if is_live:
            group_key = _preferred_row_identity(row) or row.id
            active_groups[group_key].append(row)
            continue

        if _row_age_seconds(row, now) < stale_seconds:
            kept += 1
            continue

        rows_to_close.append((row, 'missing_from_openclaw_truth'))

    for _group_key, group_rows in active_groups.items():
        if len(group_rows) == 1:
            kept += 1
            continue

        ordered = sorted(
            group_rows,
            key=lambda row: (
                getattr(row, 'started_at', now),
                row.id,
            ),
            reverse=True,
        )
        kept += 1
        for duplicate in ordered[1:]:
            rows_to_close.append((duplicate, 'superseded_duplicate_active_row'))

    for row, reason in rows_to_close:
        closed += await _close_rows([row], now, reason)

    return {
        'active_truth_identifiers': len(active_identifiers),
        'active_rows_seen': len(active_rows),
        'closed': closed,
        'kept': kept,
    }
