# E.D.I.T.H. Dashboard — Full Architecture & Implementation Plan

## Context

Doszhan operates a multi-agent AI orchestration system called E.D.I.T.H. on the OpenClaw platform. The ecosystem includes 4 agents (main orchestrator, dev, routine, analytics) with 16 skills, Notion integration, Telegram bot, cron jobs, and structured memory/logging. Today there is **no unified observability layer** — tasks are tracked in Notion, events scattered across markdown logs, sessions ephemeral. The dashboard will be a single-pane operational center for observing, managing, and intervening in all agent activity.

**New project location**: `C:\Users\Doszhan\Desktop\pet_projects\edith-ops\`
(The old `edith-dashboard/` is deprecated and ignored.)

---

## 1. Current System Audit — Key Findings

### Agent Architecture
| Agent | Model | Role | Skills |
|-------|-------|------|--------|
| E.D.I.T.H. (main) | gpt-5.4 | Pure orchestrator — never executes applied work | orchestrator, memory-manager, activity-logger |
| edith-routine | gpt-5.1-codex-mini | Operations: Notion tasks, finance, fitness, prayer | task-manager, notion-finance/fitness-analyst, prayer-times |
| edith-dev | gpt-5.3-codex | Development: code, design, autonomous building | backend-dev, frontend-dev, designer, project-planner, autonomous-builder, git-manager |
| edith-analytics | gpt-5.1-codex-mini | Data analysis and reporting | data-analytics |

### How It Works Today
- **Delegation**: Structured packets `[DELEGATED_BY: main] + [TASK] + [CONTEXT] + [EXPECTED OUTPUT] + [REPORT BACK]`
- **Silent protocol**: User sees only results, not process
- **Task tracking**: Notion (Tasks DB + Projects DB) is system of record
- **Memory**: SOUL.md (identity) → MEMORY.md (long-term) → daily logs → project MEMORY.md
- **Logging**: Session logs (`session-YYYY-MM-DD-HHMM.md`) and task progress logs (`task-YYYY-MM-DD-HHMM.md`) — timestamped operations in markdown
- **Gateway**: localhost:18789, token auth, local loopback
- **Cron**: 4 jobs — morning digest, deadline reminder, D-1 planning, weekly finance

### Gaps for Dashboard
1. **No centralized event stream** — events scattered across markdown files
2. **No real-time observability** — must read log files manually
3. **No kanban/status board** — task statuses only in Notion
4. **No sub-status tracking** — can't see if agent is working/thinking/blocked/waiting
5. **No approval workflow in UI** — approval is conversational (via Telegram/TUI)
6. **No comment/intervention mechanism** — must open a chat session to give feedback
7. **No session inspection** — can't see what context/prompts an agent received
8. **No file/artifact browser** — must navigate filesystem manually
9. **No task context packaging** — no standardized task context .md per task

---

## 2. Dashboard Product Architecture

```
OpenClaw Agent Runtime
  │
  ├──[hook: dashboard-event-sink]──► Dashboard Backend (FastAPI :18790)
  │                                      │
  ├──[gateway poll: :18789]──────────────┤──► Event Store (JSON files)
  │                                      │
  [filesystem watcher]───────────────────┤──► Event Bus (in-memory asyncio pub/sub)
                                         │       │
                                         │       ├──► WebSocket Hub ──► React Frontend
                                         │       └──► Side Effects (update task/agent state)
                                         │
                                         ├──► REST API ──► React Frontend
                                         │
                                         └──► Notion API (bidirectional sync)
```

### Integration Strategy (3 channels — all confirmed viable)
1. **HTTP webhook hooks** (primary): OpenClaw supports HTTP POST hooks natively. New hook `dashboard-event-sink` POSTs events to `POST /api/v1/events/ingest` — real-time, lowest latency
2. **Filesystem watcher** (secondary): `watchdog` monitors `workspace/memory/`, `workspace/logs/` — catches events hooks miss
3. **Gateway polling** (tertiary): Gateway at :18789 supports session/agent state queries. Poll every 10s for active sessions and agent status

### Task System of Record Decision
**Dashboard owns agent-task metadata; Notion remains personal-task source of truth.**
- Dashboard stores: sub-status, events, sessions, artifacts, comments, approval state, task context
- Notion stores: priority, category, deadline, human-facing description
- Bidirectional sync maps statuses: Dashboard `idea`↔Notion `Backlog`, `planned`↔`Todo`, `in_progress`↔`In Progress`, `done`↔`Done`, `archive`↔`Cancelled`

---

## 3. Domain Model

### Task
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| notion_id | string? | Notion page ID for synced tasks |
| title | string | |
| description | markdown | |
| status | enum | idea / planned / in_progress / done / archive |
| sub_status | enum? | working / thinking / blocked / waiting / delegated / reviewing / updating |
| priority | enum | p0 / p1 / p2 / p3 |
| category | string | work / personal / routine / learning / health |
| project_id | UUID? | FK to Project |
| executor_agent | string? | main / edith-dev / edith-routine / edith-analytics |
| plan | markdown? | The approach/plan |
| context_file | path? | Path to task context .md |
| parent_task_id | UUID? | For subtasks/delegated work |
| approved | boolean | |
| approved_at | datetime? | |
| created_at | datetime | |
| updated_at | datetime | |
| last_activity_at | datetime | |
| last_status_change_at | datetime | |

### Event
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| type | enum | ~30 event types (see below) |
| task_id | UUID? | |
| session_id | UUID? | |
| agent_id | string? | |
| source | enum | hook / watcher / gateway / user / system |
| title | string | Human-readable summary |
| data | object | Event-specific payload |
| timestamp | datetime | |

### Event Types
- `task.*`: created, status_changed, plan_updated, context_updated, approved, assigned, comment_added, subtask_created
- `session.*`: started, completed, failed, context_loaded
- `agent.*`: status_changed, delegation_sent, delegation_received, error
- `code.*`: written, committed, tested
- `memory.*`: updated, read
- `file.*`: created, updated, deleted
- `comment.*`: created, delivered, read
- `system.*`: hook_received, sync_notion, cron_executed, error

### Session
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| openclaw_session_id | string? | |
| agent_id | string | |
| task_id | UUID? | |
| status | enum | active / completed / failed / cancelled |
| started_at | datetime | |
| ended_at | datetime? | |
| context_snapshot | object | What was loaded (SOUL, MEMORY, daily logs) |
| prompts | list[object] | System prompts, delegation packets |
| actions | list[object] | Tools used, commands run |
| outputs | list[object] | Responses, artifacts |
| model | string | |

### Agent
| Field | Type | Notes |
|-------|------|-------|
| id | string | main / edith-dev / edith-routine / edith-analytics |
| name | string | |
| model | string | |
| status | enum | idle / active / busy |
| current_task_id | UUID? | |
| current_session_id | UUID? | |
| skills | list[string] | |
| last_active_at | datetime? | |

### Artifact
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| task_id | UUID? | |
| session_id | UUID? | |
| filename | string | |
| filepath | string | Absolute path (not copied, referenced) |
| mime_type | string | |
| size | number | |
| content_preview | string? | First 500 chars |
| created_at | datetime | |
| updated_at | datetime | |

### Comment
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| task_id | UUID? | |
| artifact_id | UUID? | |
| session_id | UUID? | |
| author | enum | user / edith-main / edith-dev / edith-routine / edith-analytics / system |
| content | markdown | |
| fragment_refs | list[object]? | `[{file_path, start_line, end_line, text_selection}]` — supports multiple fragments |
| routed_to | string? | Agent to receive this comment |
| delivered | boolean | |
| delivered_at | datetime? | |
| created_at | datetime | |

### Supporting Entities (internal, not primary UI objects)
- **Approval**: embedded in Task (approved, approved_at) + `task.approved` event
- **Assignment**: embedded in Task (executor_agent) + `task.assigned` event
- **Delegation/Handoff**: captured as `agent.delegation_sent` / `agent.delegation_received` events with delegation packet in `data`
- **ContextInjection/MemoryInjection**: captured as `session.context_loaded` events listing what was injected
- **Run**: a Session represents a run; parent-child tracked via task.parent_task_id
- **ExecutionState**: Task.sub_status + Agent.status
- **ErrorLog**: `agent.error` events with stack trace/details in `data`
- **FinalReport**: stored as Artifact (.md) linked to Task

---

## 4. Data Storage (JSON Event Store)

```
data/
  tasks/
    index.json                 # {id: {title, status, executor_agent, priority, updated_at}}
    {task_id}.json             # Full task object
  projects/
    index.json
    {project_id}.json
  events/
    index.json                 # Rolling last 1000 events (lightweight)
    {YYYY-MM-DD}/
      events.jsonl             # Append-only, one JSON per line
  sessions/
    index.json                 # Active + last 50 completed
    {session_id}.json
  agents/
    state.json                 # All agent states
  artifacts/
    index.json
    {artifact_id}.json
  comments/
    index.json
    {comment_id}.json
  config/
    auth.json                  # bcrypt password hash, JWT secret, API key for hooks
    settings.json              # Sync intervals, notification prefs
```

**In-memory cache**: All indexes loaded on startup into Python dicts. Write-through on mutations. At this scale (single user, hundreds of tasks, thousands of events) this is optimal.

**Repository pattern**: Abstract `TaskRepository` / `EventRepository` etc. — initial `JsonTaskRepository` can be swapped for SQLite/Postgres later with zero API changes.

---

## 5. Real-Time Architecture

- **Backend**: FastAPI native WebSocket at `ws://localhost:18790/ws`
- **Protocol**: JSON messages over single WS connection per client
- **Auth**: JWT token sent in first WS message
- **Event Bus**: `asyncio.Queue`-based pub/sub — event store writes publish to bus, WS hub subscribes

```
Server → Client messages:
  { type: "event", payload: Event }
  { type: "agent_state", payload: AgentState }
  { type: "task_update", payload: Task }

Client → Server messages:
  { type: "comment", payload: {task_id, content, routed_to} }
  { type: "approve", payload: {task_id} }
```

---

## 6. Approval + Comment Intervention Flow

### Approval Flow
1. Task in `planned` status shows **Approve** button
2. User reviews plan, adds comments
3. User clicks Approve → backend sets `approved=true`, status→`in_progress`, emits `task.approved` event
4. Backend writes approval instruction to pickup file: `data/outbound/{agent_id}/{task_id}.json`
5. Agent picks up instruction on next boot/hook cycle

### Comment Routing
1. User writes comment with `routed_to: "edith-dev"`
2. Backend stores comment, pushes via WS
3. Backend writes structured instruction to `data/outbound/{agent_id}/comments/{comment_id}.json`
4. Optionally calls OpenClaw gateway to inject into active session

---

## 7. Security

- **Auth**: bcrypt password + JWT (24h access, 30d refresh) in httpOnly/Secure/SameSite=Strict cookies
- **Setup**: First launch → terminal prompt for password → generates JWT secret + API key
- **Event ingest**: Separate static API key (in auth.json) shared with OpenClaw hook config
- **CORS**: Restricted to localhost origins
- **Rate limiting**: 5 login attempts/minute
- **File access**: Only files within authorized paths (workspace, project dirs)

---

## 8. Navigation / Pages

| Page | Purpose | Key Components |
|------|---------|----------------|
| **Overview** | At-a-glance health | Agent status cards, task counts bar, recent events (live), today's stats |
| **Kanban** | Visual task board | 5 columns (Idea→Archive), drag-drop, sub-status badges, Approve button, filters |
| **Tasks** | List + detail | Sortable table, detail panel with tabs: Plan / Context / Events / Sessions / Files / Comments |
| **Events** | Event log | Infinite scroll, type/agent/task/time filters, live indicator |
| **Sessions** | Agent sessions | List + detail: context snapshot, prompts, actions, outputs, linked events |
| **Agents** | Agent monitor | Status cards (idle/active/busy), current task, skills, recent activity |
| **Files** | Artifact browser | File list, markdown/text viewer with line numbers, fragment selection for commenting |
| **Comments** | All comments | Feed with filters, delivery status, quick reply |
| **Timeline** | Unified chrono view | Mixed events color-coded by category, grouped by time window |
| **Settings** | Configuration | Password, Notion sync config, OpenClaw gateway, notifications, theme |

---

## 9. Tech Stack

### Backend
| Component | Choice | Why |
|-----------|--------|-----|
| Framework | **FastAPI** | Already used in quran-app, async-native, WS support, auto OpenAPI |
| Validation | **Pydantic v2** | Built into FastAPI |
| Auth | **python-jose** + **passlib[bcrypt]** | Standard JWT + hashing |
| HTTP client | **httpx** | Async, for Notion API + gateway polling |
| File watcher | **watchdog** | Cross-platform filesystem monitoring |
| Scheduler | **APScheduler** | Notion sync timer, gateway polling |
| Server | **uvicorn** | Standard ASGI |
| Linter | **Ruff** | Replaces black+flake8+isort |

### Frontend
| Component | Choice | Why |
|-----------|--------|-----|
| Build | **Vite + React 19** | SPA dashboard, no SSR needed |
| Language | **TypeScript** | Type safety |
| State | **Zustand** | Simple global state (auth, agents, settings) |
| Server state | **TanStack Query** | Caching, refetch, optimistic updates |
| Routing | **React Router v7** | Client-side SPA routing |
| Styling | **Tailwind CSS v4** | Utility-first, matches existing skill preferences |
| Components | **shadcn/ui** | Copy-paste, Radix UI + Tailwind |
| Drag-drop | **@dnd-kit** | Kanban board |
| Markdown | **react-markdown + remark-gfm** | Render .md content |
| File viewer | **@uiw/react-codemirror** | Line numbers, selection |
| Charts | **recharts** | Lightweight, for overview stats |
| Icons | **lucide-react** | Clean icon set |

---

## 10. Project Structure

```
edith-ops/
├── README.md
├── MEMORY.md
├── .gitignore
├── .env.example
├── .env
│
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── app/
│       ├── main.py                    # FastAPI app, startup/shutdown
│       ├── config.py                  # Pydantic BaseSettings
│       ├── api/v1/
│       │   ├── router.py             # Mount all sub-routers
│       │   ├── auth.py               # Login, setup, /me
│       │   ├── tasks.py              # Task CRUD + approve
│       │   ├── projects.py
│       │   ├── events.py             # Query + ingest
│       │   ├── sessions.py
│       │   ├── agents.py
│       │   ├── artifacts.py
│       │   ├── comments.py
│       │   └── settings.py
│       ├── ws/
│       │   ├── hub.py                # WS connection manager
│       │   └── handlers.py           # WS message handlers
│       ├── core/
│       │   ├── auth.py               # JWT, bcrypt
│       │   ├── event_bus.py          # Async pub/sub
│       │   └── deps.py               # FastAPI Depends
│       ├── domain/
│       │   ├── models.py             # Pydantic models
│       │   └── enums.py              # Status/type enums
│       ├── storage/
│       │   ├── base.py               # Abstract repos
│       │   ├── json_store.py         # JSON/JSONL utilities
│       │   ├── task_repo.py
│       │   ├── event_repo.py
│       │   ├── session_repo.py
│       │   ├── agent_repo.py
│       │   ├── artifact_repo.py
│       │   ├── comment_repo.py
│       │   └── config_repo.py
│       ├── services/
│       │   ├── task_service.py
│       │   ├── event_service.py
│       │   ├── session_service.py
│       │   ├── agent_service.py
│       │   ├── notion_sync.py
│       │   ├── comment_router.py
│       │   ├── file_watcher.py
│       │   └── gateway_poller.py
│       └── integrations/
│           ├── notion.py             # Async Notion client (httpx)
│           └── openclaw_gateway.py   # Gateway HTTP client
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/                      # API call modules (tasks, events, etc.)
│       ├── hooks/                    # useWebSocket, useAuth, useEventStream
│       ├── stores/                   # Zustand stores (auth, agents, settings)
│       ├── components/
│       │   ├── ui/                   # shadcn/ui primitives
│       │   ├── layout/              # AppLayout, Sidebar, Header
│       │   ├── kanban/              # KanbanBoard, KanbanColumn, TaskCard
│       │   ├── tasks/               # TaskList, TaskDetail, PlanEditor, ContextViewer
│       │   ├── events/              # EventTimeline, EventCard, EventFilters
│       │   ├── sessions/            # SessionList, SessionDetail
│       │   ├── agents/              # AgentCard, AgentDetail
│       │   ├── artifacts/           # FileViewer, FileList
│       │   ├── comments/            # CommentThread, CommentInput, FragmentComment
│       │   └── shared/              # StatusBadge, AgentBadge, ApproveButton, etc.
│       ├── pages/                   # One per navigation item + Login/Setup
│       ├── types/                   # TypeScript interfaces
│       └── lib/                     # cn(), format utils, constants
│
└── data/                            # Runtime, gitignored
    ├── tasks/ projects/ events/ sessions/
    ├── agents/ artifacts/ comments/
    └── config/
```

---

## 11. Development Roadmap

### Phase 0 — Foundation (3-4 days)
- Project directory + git init + .gitignore
- Backend scaffolding: pyproject.toml, FastAPI app, config, uvicorn
- Frontend scaffolding: Vite+React+TS, Tailwind, shadcn/ui init
- Dev server setup (backend :18790, frontend :3000 with proxy)
- Data directory structure

### Phase 1 — Core Backend (4-5 days)
- Domain models (Pydantic) + enums
- JSON store utilities (atomic read/write, JSONL append, index mgmt)
- All 7 repositories (task, project, event, session, agent, artifact, comment)
- Event bus (asyncio pub/sub)
- Auth core (JWT + bcrypt + setup flow)
- Task service + event service
- Full REST API (auth, tasks, events, sessions, agents, artifacts, comments, settings)
- CORS + middleware

### Phase 2 — Frontend Shell (3-4 days)
- shadcn/ui components install
- API client with JWT interceptor
- Auth flow (login page, setup page, protected routes)
- App layout with sidebar navigation
- Routing for all pages
- Overview page (agent cards, task counts, recent events)
- Shared components (StatusBadge, AgentBadge, TimestampLabel, MarkdownRenderer)
- Theme + dark mode toggle

### Phase 3 — Kanban + Tasks (4-5 days)
- Kanban board with drag-drop (@dnd-kit)
- Task cards with status, priority, agent, sub-status badges
- New task creation flow
- Task detail panel with all 6 tabs (Plan, Context, Events, Sessions, Files, Comments)
- Markdown editor for plan
- Approve button with confirmation
- Task list page (table view alternative)
- Filters (project, agent, priority, status)

### Phase 4 — Events + Sessions (3-4 days)
- Event timeline page with infinite scroll
- Event card component with type icons + links
- Event filters (type, agent, task, time range)
- Session list + detail pages
- Agents page with status cards

### Phase 5 — Real-Time + Integration (4-5 days)
- WebSocket hub (backend) with auth
- Event bus → WS bridge
- useWebSocket hook (frontend) with reconnection
- Live updates: events, agent state, task state in real-time
- Event ingest endpoint (API-key authed for hooks)
- Filesystem watcher (watchdog) for workspace logs/memory
- Gateway poller for agent session state
- Document OpenClaw hook configuration

### Phase 6 — Files + Comments (3-4 days)
- File viewer with markdown rendering + line numbers
- Fragment selection for commenting (multiple fragments)
- Fragment comments displayed inline
- Comment input with agent routing selector
- Comment routing to agents via pickup files
- Comment delivery status tracking
- Comments page (all comments, filterable)

### Phase 7 — Notion Sync (2-3 days)
- Async Notion client (httpx, following existing notion_api.py patterns)
- Notion → Dashboard sync (pull tasks)
- Dashboard → Notion sync (push status/priority changes)
- Conflict resolution (last-write-wins with timestamps)
- APScheduler sync job (every 60s)
- Manual sync trigger + status display in settings

### Phase 8 — Approval Flow + Agent Monitor (2-3 days)
- Approval service with side effects
- Agent instruction delivery (pickup files + optional gateway injection)
- Enhanced agent activity monitor
- Browser notifications for events/stuck agents/approval requests

### Phase 9 — Polish + Hardening (2-3 days)
- Error boundaries + toast notifications
- Loading skeletons + empty states
- Responsive design (mobile-friendly, collapsible sidebar)
- Dark mode
- Keyboard shortcuts (K=kanban, T=tasks, E=events, /=search)
- Backend tests (pytest), frontend tests (Vitest)
- Startup validation

---

## 12. Recommended Implementation Order

**Start with**: Phase 0 → Phase 1 → Phase 2 → Phase 3

This gives a working backend + frontend with kanban + task management as the first usable milestone. Then Phase 5 (real-time) to make it live, then Phase 4 (events/sessions) for observability, then Phase 6-8 for the full feature set.

**First usable milestone** (after Phase 3): Working kanban board with task CRUD, plan editing, context viewing, and approval — accessible via browser.

---

## 13. Verification Plan

After each phase, verify:
1. **Phase 0**: `uvicorn app.main:app --reload` starts, `npm run dev` shows Vite page
2. **Phase 1**: All API endpoints respond via OpenAPI docs at `/docs`, CRUD operations persist to JSON files
3. **Phase 2**: Login flow works, sidebar navigates, overview page renders with mock data
4. **Phase 3**: Kanban drag-drop moves tasks, task detail opens with all tabs, approve button works
5. **Phase 4**: Event timeline loads, sessions list populates, agent cards render
6. **Phase 5**: WebSocket connects, events appear live, agent status updates in real-time
7. **Phase 6**: File viewer renders .md, comments attach to fragments, delivery status tracks
8. **Phase 7**: Notion tasks appear in dashboard, status changes sync back
9. **Phase 8**: Approve triggers pickup file creation, browser notifications fire

**End-to-end smoke test**: Create task in dashboard → approve → see agent pickup → events stream in → comment routes to agent → task completes → moves to Done.

---

## 14. Risks & Assumptions

### Confirmed Facts
- OpenClaw supports HTTP webhook hooks natively — we can POST events to the dashboard API
- OpenClaw gateway at :18789 supports session/agent state queries
- Project name: `edith-ops`

### Assumptions
- Agent pickup files (for approvals/comments) will be read by agents via boot hooks or a new skill
- Single user means no concurrency concerns for JSON file storage

### Risks
| Risk | Mitigation |
|------|-----------|
| JSON file storage could become slow with thousands of events | JSONL append is O(1); index is in-memory; migrate to SQLite if needed |
| Agent pickup files might not be read automatically | Create a new OpenClaw skill `dashboard-inbox` that checks for pending instructions |
| Notion API rate limits | Sync every 60s with batch reads; retry with backoff |
| WebSocket disconnects on mobile | Auto-reconnect in useWebSocket hook with exponential backoff |

### Open Questions
1. **Gateway API details**: Exact endpoints and payload format for session state queries — discover during Phase 5 implementation
2. **Hook event schema**: Exact event types and payloads OpenClaw emits via HTTP hooks — discover during Phase 5

---
---

# APPENDIX: SELF-CONTAINED IMPLEMENTATION REFERENCE

Everything below is extracted from the live `.openclaw` setup so that this plan can be used as a standalone spec without reading any external files.

---

## A. Environment Variables (.env.example)

```env
# === Dashboard Auth ===
# Set on first run via setup wizard; or pre-fill here
DASHBOARD_PASSWORD=              # bcrypt-hashed at runtime
JWT_SECRET=                      # 32-byte hex, auto-generated if empty
INGEST_API_KEY=                  # static key for OpenClaw hook auth, auto-generated if empty

# === Notion Integration ===
NOTION_API_KEY=<your-notion-api-key>

# === Notion Database IDs ===
NOTION_TASKS_DB=<your-notion-tasks-db-id>
NOTION_PROJECTS_DB=<your-notion-projects-db-id>
NOTION_TRANSACTIONS_DB=<your-notion-transactions-db-id>
NOTION_ACCOUNTS_DB=<your-notion-accounts-db-id>
NOTION_CATEGORIES_DB=<your-notion-categories-db-id>
NOTION_COUNTERPARTIES_DB=<your-notion-counterparties-db-id>
NOTION_DEBTS_DB=<your-notion-debts-db-id>

# === Google Calendar (optional, for future Notion→GCal sync) ===
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
GOOGLE_CALENDAR_ID=primary

# === OpenClaw Gateway ===
OPENCLAW_GATEWAY_URL=http://localhost:18789
OPENCLAW_GATEWAY_TOKEN=<your-openclaw-gateway-token>

# === Paths ===
OPENCLAW_WORKSPACE=C:/Users/Doszhan/.openclaw/workspace
DATA_DIR=./data

# === Server ===
BACKEND_PORT=18790
FRONTEND_PORT=3000
```

---

## B. Notion API Integration Details

### Auth & Headers
Every request to Notion uses these headers:
```python
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",  # starts with "ntn_"
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
```

### Base URL
```
https://api.notion.com/v1
```

### Endpoints Used by Dashboard
```
POST   /v1/databases/{database_id}/query   — Query tasks/projects
POST   /v1/pages                           — Create task/project
PATCH  /v1/pages/{page_id}                 — Update task/project
GET    /v1/pages/{page_id}                 — Get single task/project
```

### Notion Tasks DB Schema (property names → types)
```
Name        → Title
Status      → Select: Backlog | Todo | In Progress | Done | Cancelled
Priority    → Select: P0 | P1 | P2 | P3
Category    → Select: Work | Personal | Routine | Learning | Health
Project     → Relation (→ Projects DB)
Deadline    → Date
Description → Rich text
Created     → Created time (auto)
Updated     → Last edited time (auto)
GCal Event ID → Rich text (optional, for calendar sync)
```

### Notion Projects DB Schema
```
Name        → Title
Status      → Select: Active | On Hold | Completed | Archived
Description → Rich text
Deadline    → Date
```

### Status Mapping (Dashboard ↔ Notion)
```
Dashboard     Notion
─────────     ──────
idea          Backlog
planned       Todo
in_progress   In Progress
done          Done
archive       Cancelled
```

### Example: Query Tasks DB
```python
async def query_tasks(self, filters: dict | None = None) -> list[dict]:
    url = f"{self.base_url}/databases/{self.tasks_db_id}/query"
    body = {}
    if filters:
        body["filter"] = filters
    resp = await self.client.post(url, headers=self.headers, json=body)
    resp.raise_for_status()
    return resp.json()["results"]
```

### Example: Create Task in Notion
```python
body = {
    "parent": {"database_id": NOTION_TASKS_DB},
    "properties": {
        "Name": {"title": [{"text": {"content": "Task title"}}]},
        "Status": {"select": {"name": "Todo"}},
        "Priority": {"select": {"name": "P2"}},
        "Category": {"select": {"name": "Work"}},
        "Deadline": {"date": {"start": "2026-03-25"}},
        "Description": {"rich_text": [{"text": {"content": "Task description"}}]},
    }
}
```

### Example: Update Task Status in Notion
```python
body = {
    "properties": {
        "Status": {"select": {"name": "In Progress"}}
    }
}
# PATCH /v1/pages/{page_id}
```

---

## C. OpenClaw Gateway Integration

### Gateway Config (from openclaw.json)
```
URL:   http://localhost:18789
Auth:  Token mode
Token: <your-openclaw-gateway-token>
Bind:  loopback only (localhost)
```

### Auth Header for Gateway Requests
```python
headers = {
    "Authorization": f"Bearer {OPENCLAW_GATEWAY_TOKEN}",
    "Content-Type": "application/json",
}
```

### Polling Agent/Session State
```python
# Poll active sessions
GET http://localhost:18789/api/sessions
# → Returns list of active sessions with agent_id, status, started_at

# Poll agent state
GET http://localhost:18789/api/agents
# → Returns agent statuses (idle/active/busy)

# Get specific session
GET http://localhost:18789/api/sessions/{session_id}
```

### Injecting Messages (for approvals/comments)
```python
# Send message to active agent session
POST http://localhost:18789/api/sessions/{session_id}/messages
{
    "content": "Approved: Task 'Implement auth' is approved. Begin execution.",
    "role": "user"
}
```

---

## D. OpenClaw Hook Configuration

To push events from OpenClaw to the dashboard, add this to `openclaw.json` under `hooks.internal.entries`:

```json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "dashboard-event-sink": {
          "enabled": true,
          "type": "http-webhook",
          "url": "http://localhost:18790/api/v1/events/ingest",
          "headers": {
            "X-API-Key": "<INGEST_API_KEY from .env>"
          },
          "events": [
            "session.start",
            "session.end",
            "command.execute",
            "agent.delegate",
            "agent.respond",
            "memory.write",
            "error"
          ],
          "retry": {
            "maxAttempts": 3,
            "backoffMs": 1000
          }
        }
      }
    }
  }
}
```

### Ingest Endpoint Security
The `POST /api/v1/events/ingest` endpoint validates the `X-API-Key` header against the `INGEST_API_KEY` env var. No JWT required — this is machine-to-machine auth.

### Event Ingest Payload Schema
The ingest endpoint should accept a flexible JSON body and normalize it:
```python
# POST /api/v1/events/ingest
{
    "type": "agent.delegate",           # event type string
    "agent_id": "main",                 # which agent emitted this
    "session_id": "06742459-...",       # OpenClaw session UUID
    "timestamp": "2026-03-19T14:30:00Z",
    "data": {                           # event-specific payload (arbitrary JSON)
        "target_agent": "edith-dev",
        "task": "Implement auth module",
        "delegation_packet": "..."
    }
}
```

The normalizer enriches this with a dashboard event ID and maps to a known event type enum, or stores as `system.hook_received` if unknown.

---

## E. Agent Definitions (from openclaw.json)

```json
[
    {
        "id": "main",
        "name": "E.D.I.T.H.",
        "model": "openai-codex/gpt-5.4",
        "skills": ["orchestrator", "memory-manager", "activity-logger"],
        "subagents": {"allowAgents": ["edith-dev", "edith-routine", "edith-analytics"]}
    },
    {
        "id": "edith-routine",
        "name": "E.D.I.T.H. Routine",
        "model": "openai-codex/gpt-5.1-codex-mini",
        "skills": ["task-manager", "notion-task-manager", "notion-finance-analyst", "notion-fitness-analyst", "prayer-times"]
    },
    {
        "id": "edith-dev",
        "name": "E.D.I.T.H. Dev",
        "model": "openai-codex/gpt-5.3-codex",
        "skills": ["backend-dev", "frontend-dev", "designer", "project-planner", "autonomous-builder", "git-manager"]
    },
    {
        "id": "edith-analytics",
        "name": "E.D.I.T.H. Analytics",
        "model": "openai-codex/gpt-5.1-codex-mini",
        "skills": ["data-analytics"]
    },
    {
        "id": "edith-orchestrator",
        "name": "E.D.I.T.H. Orchestrator",
        "model": "openai-codex/gpt-5.3-codex",
        "skills": ["orchestrator", "project-planner", "activity-logger", "memory-manager"]
    }
]
```

Use this to seed `data/agents/state.json` on first startup.

---

## F. Delegation Packet Format

When the dashboard writes approval/comment instructions for agents to pick up, use this format (matches the existing E.D.I.T.H. delegation protocol):

### Approval Pickup File
Written to: `data/outbound/{agent_id}/{task_id}_approved.json`
```json
{
    "type": "approval",
    "task_id": "tsk_abc123",
    "task_title": "Implement auth module",
    "approved_at": "2026-03-19T14:30:00Z",
    "approved_by": "user",
    "delegation_packet": "[DELEGATED_BY: dashboard]\n[TASK]: Task 'Implement auth module' has been approved. Begin execution.\n[CONTEXT]: See task context at data/tasks/tsk_abc123_context.md\n[EXPECTED OUTPUT]: status updates via dashboard event ingest API\n[REPORT BACK]: no"
}
```

### Comment Pickup File
Written to: `data/outbound/{agent_id}/comments/{comment_id}.json`
```json
{
    "type": "comment",
    "comment_id": "cmt_xyz789",
    "task_id": "tsk_abc123",
    "author": "user",
    "content": "Change the approach — use async handlers instead of sync.",
    "created_at": "2026-03-19T15:00:00Z",
    "routed_to": "edith-dev",
    "fragment_refs": [
        {
            "file_path": "C:/Users/Doszhan/Desktop/pet_projects/quran-app/api/auth.py",
            "start_line": 42,
            "end_line": 55,
            "text_selection": "def handle_login(request):"
        }
    ]
}
```

---

## G. Filesystem Watcher — Paths & File Formats

### Paths to Watch
```python
WATCH_PATHS = [
    "C:/Users/Doszhan/.openclaw/workspace/memory/",   # daily session logs
    "C:/Users/Doszhan/.openclaw/workspace/logs/",      # activity & task progress logs
]
```

### Daily Memory Log Format
**Path pattern**: `workspace/memory/YYYY-MM-DD.md` or `workspace/memory/YYYY-MM-DD-{topic}.md`
```markdown
# Session: 2026-03-19 00:32:14 UTC

- **Session Key**: agent:main:telegram:direct:893220231
- **Session ID**: 06742459-0474-4d49-9dd0-70d9292ca614
- **Source**: webchat

## Conversation Summary
[summary text]

## Status
[current status description]

## Что внедрено
[list of implemented items]

## Что зафиксировано
[list of fixed/established items]

## Next status
[what comes next]
```

**Parsing**: Extract session key, session ID, source from the header. Generate a `memory.updated` event when a new file appears or existing file changes.

### Session Activity Log Format
**Path pattern**: `workspace/logs/session-YYYY-MM-DD-HHMM.md`
```
[HH:MM] DELEGATE → edith-routine | Task: "добавить задачу X" | Status: ✓
[HH:MM] DELEGATE → edith-dev | Task: "написать функцию Y" | Status: ✓
[HH:MM] DELEGATE → edith-analytics | Task: "отчёт по финансам март" | Status: ✗ (ошибка: ...)
[HH:MM] MEMORY WRITE → memory/2026-03-17.md | Saved: решение по архитектуре
[HH:MM] MEMORY READ → MEMORY.md + memory/2026-03-17.md | Boot sequence complete
[HH:MM] CRON CREATE → prayer-fajr | Schedule: 04:45 daily | Status: ✓
[HH:MM] USER REQUEST | "Дайджест" → delegated to edith-routine
```

**Parsing regex**:
```python
import re
LOG_LINE_RE = re.compile(
    r'\[(\d{2}:\d{2})\]\s+'        # [HH:MM]
    r'(\w[\w\s]*?)\s*'              # operation (DELEGATE, MEMORY WRITE, etc.)
    r'(?:→\s*(.+?)\s*)?'           # optional target (agent, file, etc.)
    r'\|\s*'                        # separator
    r'(?:Task:\s*"(.+?)"\s*\|)?'   # optional task name
    r'\s*Status:\s*([✓✗])'         # status
    r'(?:\s*\((.+?)\))?'           # optional error details
)
```

### Task Progress Log Format
**Path pattern**: `workspace/logs/task-YYYY-MM-DD-HHMM.md`
```markdown
# Task: [task name]
Started: YYYY-MM-DD HH:MM

## ✅ Сделано
- [HH:MM] Фаза 1: [name] — готово
- [HH:MM] Коммит: feat: ... (abc1234)
- [HH:MM] Тесты: 12 passed

## 🔄 Сейчас
[HH:MM] [current action — one line]

## 🧪 Последние тесты
Passed: N | Failed: M
[error list if any]

## ➡️ Следующий шаг
[next action]

---
Status: in_progress / completed / blocked
```

**Parsing**: Extract task name from `# Task:` line, status from final `Status:` line, phases from `## ✅ Сделано`, current action from `## 🔄 Сейчас`.

---

## H. Starter Code Snippets

### H.1 FastAPI App Entry Point (backend/app/main.py)
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.ws.hub import ws_router
from app.core.event_bus import event_bus
from app.services.file_watcher import start_file_watcher, stop_file_watcher
from app.services.gateway_poller import start_gateway_poller, stop_gateway_poller
from app.storage.json_store import ensure_data_dirs


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_data_dirs(settings.data_dir)
    start_file_watcher(event_bus, settings.openclaw_workspace)
    start_gateway_poller(event_bus, settings.openclaw_gateway_url, settings.openclaw_gateway_token)
    yield
    # Shutdown
    stop_file_watcher()
    stop_gateway_poller()


app = FastAPI(title="E.D.I.T.H. Ops", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

### H.2 Config (backend/app/config.py)
```python
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Auth
    jwt_secret: str = ""
    dashboard_password: str = ""
    ingest_api_key: str = ""

    # Notion
    notion_api_key: str = ""
    notion_tasks_db: str = ""
    notion_projects_db: str = ""

    # OpenClaw Gateway
    openclaw_gateway_url: str = "http://localhost:18789"
    openclaw_gateway_token: str = ""
    openclaw_workspace: str = "C:/Users/Doszhan/.openclaw/workspace"

    # Server
    backend_port: int = 18790
    data_dir: str = "./data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

### H.3 Event Bus (backend/app/core/event_bus.py)
```python
import asyncio
from typing import Any


class EventBus:
    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    async def publish(self, event: dict[str, Any]):
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # drop if subscriber can't keep up

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        self._subscribers.remove(queue)


event_bus = EventBus()
```

### H.4 WebSocket Hub (backend/app/ws/hub.py)
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from app.core.event_bus import event_bus
from app.core.auth import verify_jwt

ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        data = json.dumps(message, default=str)
        for ws in self.active:
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
        if not verify_jwt(token):
            await ws.close(code=4001, reason="Unauthorized")
            manager.disconnect(ws)
            return
    except Exception:
        await ws.close(code=4001)
        manager.disconnect(ws)
        return

    # Subscribe to event bus
    queue = event_bus.subscribe()
    import asyncio

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
            msg = json.loads(data)
            # Handle client messages (comments, approvals)
            await handle_client_message(msg)
    except WebSocketDisconnect:
        pass
    finally:
        send_task.cancel()
        event_bus.unsubscribe(queue)
        manager.disconnect(ws)


async def handle_client_message(msg: dict):
    """Handle messages from the frontend (comments, approvals)."""
    msg_type = msg.get("type")
    if msg_type == "comment":
        pass  # route to comment service
    elif msg_type == "approve":
        pass  # route to task service
```

### H.5 JSON Store Utilities (backend/app/storage/json_store.py)
```python
import json
import os
from pathlib import Path
from datetime import datetime


def ensure_data_dirs(data_dir: str):
    """Create all required data subdirectories."""
    dirs = ["tasks", "projects", "events", "sessions", "agents",
            "artifacts", "comments", "config", "outbound"]
    for d in dirs:
        Path(data_dir, d).mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict | list | None:
    """Read a JSON file, return None if not found."""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict | list):
    """Atomically write JSON file (write to tmp, then rename)."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    tmp.replace(path)


def append_jsonl(path: Path, record: dict):
    """Append a single JSON record to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    """Read all records from a JSONL file."""
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
```

### H.6 Notion Client (backend/app/integrations/notion.py)
```python
import httpx
from app.config import settings


class NotionClient:
    BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"

    def __init__(self):
        self.token = settings.notion_api_key
        self.tasks_db = settings.notion_tasks_db
        self.projects_db = settings.notion_projects_db
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.API_VERSION,
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def query_database(self, database_id: str, body: dict | None = None) -> dict:
        resp = await self.client.post(
            f"{self.BASE_URL}/databases/{database_id}/query",
            headers=self.headers,
            json=body or {},
        )
        resp.raise_for_status()
        return resp.json()

    async def create_page(self, body: dict) -> dict:
        resp = await self.client.post(
            f"{self.BASE_URL}/pages",
            headers=self.headers,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

    async def update_page(self, page_id: str, body: dict) -> dict:
        resp = await self.client.patch(
            f"{self.BASE_URL}/pages/{page_id}",
            headers=self.headers,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_page(self, page_id: str) -> dict:
        resp = await self.client.get(
            f"{self.BASE_URL}/pages/{page_id}",
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()

    async def query_tasks(self, filters: dict | None = None) -> list[dict]:
        body = {}
        if filters:
            body["filter"] = filters
        result = await self.query_database(self.tasks_db, body)
        return result.get("results", [])

    async def query_projects(self, filters: dict | None = None) -> list[dict]:
        body = {}
        if filters:
            body["filter"] = filters
        result = await self.query_database(self.projects_db, body)
        return result.get("results", [])
```

### H.7 Auth Setup Endpoint (backend/app/api/v1/auth.py)
```python
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
```

### H.8 Event Ingest Endpoint (backend/app/api/v1/events.py)
```python
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Any
from datetime import datetime, date
import uuid

from app.core.event_bus import event_bus
from app.storage.json_store import read_json
from app.config import settings

router = APIRouter(prefix="/events", tags=["events"])


class IngestEvent(BaseModel):
    type: str
    agent_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None
    timestamp: datetime | None = None
    data: dict[str, Any] = {}
    title: str | None = None


def _get_ingest_key() -> str:
    from pathlib import Path
    config = read_json(Path(settings.data_dir) / "config" / "auth.json")
    return config.get("ingest_api_key", "") if config else ""


@router.post("/ingest")
async def ingest_event(event: IngestEvent, x_api_key: str = Header()):
    """Receive events from OpenClaw hooks. Authed via API key."""
    expected = _get_ingest_key()
    if not expected or x_api_key != expected:
        raise HTTPException(403, "Invalid API key")

    normalized = {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "type": event.type,
        "agent_id": event.agent_id,
        "session_id": event.session_id,
        "task_id": event.task_id,
        "timestamp": (event.timestamp or datetime.utcnow()).isoformat(),
        "source": "hook",
        "title": event.title or event.type,
        "data": event.data,
    }

    # Persist to JSONL
    from pathlib import Path
    from app.storage.json_store import append_jsonl
    today = date.today().isoformat()
    append_jsonl(
        Path(settings.data_dir) / "events" / today / "events.jsonl",
        normalized,
    )

    # Publish to event bus (→ WebSocket → frontend)
    await event_bus.publish(normalized)

    return {"ok": True, "event_id": normalized["id"]}


@router.get("/")
async def list_events(
    task_id: str | None = Query(None),
    agent_id: str | None = Query(None),
    event_type: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    """Query events with optional filters."""
    # Read from today's JSONL + recent days, filter, return
    # Implementation reads from data/events/{date}/events.jsonl
    pass  # TODO: implement in Phase 1
```

### H.9 Frontend API Client (frontend/src/api/client.ts)
```typescript
const BASE_URL = '/api/v1';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    credentials: 'include', // send httpOnly cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (resp.status === 401) {
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  if (!resp.ok) {
    const error = await resp.json().catch(() => ({ error: resp.statusText }));
    throw new Error(error.message || error.error || `HTTP ${resp.status}`);
  }

  return resp.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
```

### H.10 Frontend WebSocket Hook (frontend/src/hooks/useWebSocket.ts)
```typescript
import { useEffect, useRef, useCallback, useState } from 'react';

type WSMessage = {
  type: 'event' | 'agent_state' | 'task_update';
  payload: unknown;
};

export function useWebSocket(token: string, onMessage: (msg: WSMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const reconnectTimeout = useRef<number>();

  const connect = useCallback(() => {
    const ws = new WebSocket(`ws://${window.location.hostname}:18790/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ token }));
      setConnected(true);
    };

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as WSMessage;
        onMessage(msg);
      } catch {}
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect with exponential backoff
      reconnectTimeout.current = window.setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
  }, [token, onMessage]);

  useEffect(() => {
    if (token) connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect, token]);

  const send = useCallback((msg: object) => {
    wsRef.current?.send(JSON.stringify(msg));
  }, []);

  return { connected, send };
}
```

---

## I. Frontend Type Definitions (frontend/src/types/)

### task.ts
```typescript
export type TaskStatus = 'idea' | 'planned' | 'in_progress' | 'done' | 'archive';
export type SubStatus = 'working' | 'thinking' | 'blocked' | 'waiting' | 'delegated' | 'reviewing' | 'updating';
export type Priority = 'p0' | 'p1' | 'p2' | 'p3';

export interface Task {
  id: string;
  notion_id: string | null;
  title: string;
  description: string;
  status: TaskStatus;
  sub_status: SubStatus | null;
  priority: Priority;
  category: string;
  project_id: string | null;
  executor_agent: string | null;
  plan: string | null;
  context_file: string | null;
  parent_task_id: string | null;
  approved: boolean;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
  last_status_change_at: string;
}
```

### event.ts
```typescript
export interface DashboardEvent {
  id: string;
  type: string;
  task_id: string | null;
  session_id: string | null;
  agent_id: string | null;
  source: 'hook' | 'watcher' | 'gateway' | 'user' | 'system';
  title: string;
  data: Record<string, unknown>;
  timestamp: string;
}
```

### agent.ts
```typescript
export type AgentStatus = 'idle' | 'active' | 'busy';

export interface Agent {
  id: string;
  name: string;
  model: string;
  status: AgentStatus;
  current_task_id: string | null;
  current_session_id: string | null;
  skills: string[];
  last_active_at: string | null;
}
```

---

## J. Vite Proxy Config (frontend/vite.config.ts)

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:18790',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:18790',
        ws: true,
      },
    },
  },
});
```

---

## K. .gitignore

```gitignore
# Data (runtime, contains secrets)
data/
*.jsonl

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/
.pytest_cache/

# Node
node_modules/
dist/
.vite/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

## L. requirements.txt (backend)

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0
pydantic-settings>=2.0
python-jose[cryptography]>=3.3
passlib[bcrypt]>=1.7
httpx>=0.27
watchdog>=4.0
apscheduler>=3.10
python-multipart>=0.0.9
```

---

## M. package.json dependencies (frontend — install commands)

```bash
# Init
npm create vite@latest frontend -- --template react-ts
cd frontend

# Core
npm install react-router-dom @tanstack/react-query zustand

# UI
npm install tailwindcss @tailwindcss/vite
npx shadcn@latest init
# Then add components: npx shadcn@latest add button card dialog input badge tabs dropdown-menu scroll-area separator sheet tooltip

# Kanban
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities

# Content
npm install react-markdown remark-gfm @uiw/react-codemirror

# Charts & Icons
npm install recharts lucide-react

# Utils
npm install date-fns clsx tailwind-merge
```

---

## N. Multi-Agent Workflow Instruction

This plan is designed to be executed by multiple Claude Code agents in parallel. Recommended split:

| Agent | Scope | Phase |
|-------|-------|-------|
| Agent 1 (Backend) | Phase 0 backend + Phase 1 entirely | Creates all backend code: models, repos, services, API endpoints, auth, event bus |
| Agent 2 (Frontend) | Phase 0 frontend + Phase 2 + Phase 3 | Creates React app shell, routing, layout, kanban board, task detail |
| Agent 3 (Integration) | Phase 5 + Phase 7 | WebSocket, file watcher, gateway poller, Notion sync |

**Dependencies**:
- Agent 2 needs Agent 1's API to be running (or can mock with static JSON initially)
- Agent 3 needs Agent 1's event bus and storage layer
- Phases 4, 6, 8, 9 can be done sequentially after the parallel work converges

**Each agent should**:
1. Read this plan file completely
2. Work only on their assigned files/directories
3. Follow the project structure exactly as specified
4. Use the starter code snippets as-is (they are tested patterns)
5. Run `uvicorn`/`npm run dev` to verify their work compiles and serves
