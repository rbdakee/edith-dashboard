# E.D.I.T.H. Dashboard — Improvement Plan

See CLAUDE.md for full project architecture. Everything described there is implemented and working. Reference it only if needed for context.

---

## 1. Sub-Tasks

Each task must support sub-tasks so the user can see how the main agent breaks work down via delegation. Example: `main` delegates code to `edith-dev` and research to `edith-analytics` — each delegation becomes a sub-task.

Sub-tasks have the same fields as tasks: title, description, context, priority, session, executor agent. Tab order in Task Detail panel: **Plan → Context → Sub-Tasks → Events → Sessions → Files**. Tabs should be horizontally scrollable.

## 2. UTC Timezone Fix

All timestamps must use UTC with a `+00:00` suffix so the frontend parses them correctly. Currently `datetime.utcnow()` produces naive datetimes — JS interprets them as local time, causing "1 hour ago" on fresh records. Fix: replace all `datetime.utcnow()` with `datetime.now(timezone.utc)`.

## 3. Sessions API for Agents

Expose current sessions to OpenClaw agents via the agent API (X-API-Key auth):
- `GET /agent/sessions` — list sessions with optional `agent_id`, `status`, `limit` filters
- `GET /agent/sessions/{session_id}` — get a single session

## 4. Event Detail Drawer + File Diff

Clicking an event card must open a detail drawer showing: session, agent, task, timestamp. For `file.*` and `memory.*` events — show file content inline (no file copying, read directly from path). Show what changed: compute unified diff between previous and current file version, visualize with green/red line highlighting. Skip tracking deletions.

Files page must show artifacts grouped by directory (collapsible tree). File viewer opens on click (split view). Support `.md`, `.py`, `.ts`, `.json`, `.txt` etc.

## 5. Comments

Current state: user writes a comment, optionally routes it to an agent, backend saves it and writes a pickup file to `data/outbound/{agent_id}/comments/{id}.json`. Agents read pending comments via `GET /agent/comments?routed_to={agent_id}` and mark them delivered via `PATCH /agent/comments/{id}/deliver`.

UX improvement: add an info hint in the comment input explaining how delivery works.

## 6. Setup Page Protection

`/setup` must redirect to `/login` if `data/config/auth.json` already exists. Anyone who knows the URL can currently register on someone else's dashboard.

## 7. Session Status Bug

Sessions stay `active` after they end because the watcher never marks them `completed`. Fix: detect session end (`.jsonl` file deleted or `reset`/`resume` in commands log) and update `Session.status` to `completed` in `session_repo`.

## 8. WebSocket "Offline" Fix

Two bugs: (1) frontend `token` is always `""` so `useWebSocket` never connects; (2) `hub.py` calls `verify_jwt(token)` without passing `secret`. Fix: add `GET /auth/ws-token` endpoint that reads JWT from httpOnly cookie and returns it in the response body. Frontend fetches it after login and passes to `useWebSocket`.
