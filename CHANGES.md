# E.D.I.T.H. Ops Dashboard — Changelog (2026-03-19)

## Summary

10 improvements shipped to the dashboard. Below is what changed and how agents can use the new capabilities.

---

## 1. UTC Timezone Fix

All timestamps across the backend now use `datetime.now(timezone.utc)` instead of `datetime.utcnow()`. Events, tasks, sessions, and comments now serialize with proper `+00:00` suffix. Frontend displays correct relative times (e.g. "just now" instead of "1 hour ago").

---

## 2. WebSocket Real-Time Connection

The "Offline" indicator in the header is now fixed. The dashboard header shows a green "Live" dot when the WebSocket is connected. Real-time updates for events, agent state, and task changes now work.

WebSocket auth was simplified — no token required (local single-user dashboard).

---

## 3. Setup Page Protection

`/setup` now redirects to `/login` if the dashboard has already been configured. Prevents accidental re-setup.

---

## 4. Session Status Bug Fixed

Sessions now correctly transition to `completed` status when an OpenClaw session ends. Previously all sessions stayed `active` indefinitely. The fix detects session end via:
- `.jsonl` file deletion in the workspace (session ended)
- `reset` or `resume` action in the commands log

---

## 5. Sessions API for Agents ✨ NEW

Agents can now query dashboard sessions via the agent API.

```
GET /api/v1/agent/sessions
  ?agent_id=edith-dev      # filter by agent
  ?status=active           # filter by status
  ?limit=20                # default 20

GET /api/v1/agent/sessions/{session_id}
```

Auth: `X-API-Key: <ingest_api_key>` header.

---

## 6. Sub-Tasks ✨ NEW

Tasks now support sub-tasks. The Task Detail panel has a new **Sub-Tasks** tab showing all child tasks. Agents can create sub-tasks via the existing task API by setting `parent_task_id`.

API:
```
GET /api/v1/tasks/?parent_task_id={task_id}   # list sub-tasks
POST /api/v1/tasks/  { "parent_task_id": "...", ... }
```

---

## 7. Events Detail + File Diff Visualization ✨ NEW

Clicking any event in the Events page opens a detail drawer showing:
- Full event metadata (agent, task, session, timestamp)
- File diff (green/red unified diff) for `file.*` and `memory.*` events
- Live file content viewer
- Raw event data (collapsible)

The file watcher now computes unified diffs between file versions and stores them in `event.data.diff`. First-time file events include a `content_snapshot`.

---

## 8. File Content API ✨ NEW

New endpoint to read file contents from the dashboard:

```
GET /api/v1/files/content?path=/absolute/path/to/file
```

Auth: JWT cookie (user-facing endpoint).
- Returns `{ content, path, filename, size, mime_type }`
- Security: only files within `openclaw_workspace` or `openclaw_dir` are accessible
- Max file size: 1MB

---

## 9. Files Page — Tree View + Viewer ✨ NEW

The Files page now shows artifacts grouped by directory (collapsible tree). Clicking a file opens a split-view panel on the right:
- Markdown files rendered with full formatting
- Code/text files shown in monospace

---

## 10. Comments API for Agents ✨ NEW

Agents can now read and acknowledge comments routed to them.

```
GET /api/v1/agent/comments?routed_to=edith-dev
# Returns undelivered comments addressed to the specified agent

PATCH /api/v1/agent/comments/{comment_id}/deliver
# Mark a comment as delivered/read
```

Auth: `X-API-Key: <ingest_api_key>` header.

### Comment pickup files
When a user writes a comment routed to an agent, a pickup file is also written to:
```
data/outbound/{agent_id}/comments/{comment_id}.json
```

Agents can either poll the API or watch the pickup file directory.

---

## Agent API Reference

Base URL: `http://localhost:18790/api/v1/agent`
Auth header: `X-API-Key: <ingest_api_key from data/config/auth.json>`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tasks` | List tasks (filter: `?status=`) |
| GET | `/tasks/{id}` | Get task |
| POST | `/tasks` | Create task |
| PATCH | `/tasks/{id}` | Update task |
| GET | `/sessions` | List sessions (filter: `?agent_id=`, `?status=`) |
| GET | `/sessions/{id}` | Get session |
| GET | `/comments` | List undelivered comments (filter: `?routed_to=`) |
| PATCH | `/comments/{id}/deliver` | Mark comment as delivered |
