# E.D.I.T.H. Ops Dashboard

Operational dashboard for the E.D.I.T.H. multi-agent AI system built on OpenClaw. Single-pane observability center for monitoring agent activity, managing tasks, and intervening in agent workflows.

## What it does

- **Real-time agent monitoring** — live status of all 4 agents (idle / active / busy) via WebSocket
- **Task management** — Kanban board + list view with sub-tasks, plans, context, approval flow
- **Event log** — full event stream from agents with file diff visualization
- **Session inspector** — view agent sessions with context snapshots and actions
- **Artifact browser** — file tree with markdown/code viewer
- **Comment routing** — send instructions to specific agents delivered as pickup files
- **Notion sync** — bidirectional task sync with Notion databases

## Stack

**Backend** — FastAPI, Pydantic v2, python-jose, watchdog, APScheduler, uvicorn
**Frontend** — React 19, TypeScript, Vite, TailwindCSS v4, shadcn/ui, TanStack Query, Zustand

## Architecture

```
OpenClaw Agent Runtime
  │
  ├── HTTP webhook hooks ──► POST /api/v1/events/ingest   (real-time events)
  ├── Filesystem watcher ──► watchdog on workspace/logs/  (file changes)
  └── Gateway polling ────► GET :18789/api/sessions       (agent state)
                                    │
                            FastAPI :18790
                                    │
                            WebSocket /ws ──► React Frontend :3000
```

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example ../.env
# Fill in your values in .env

uvicorn app.main:app --host 0.0.0.0 --port 18790 --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — first visit redirects to `/setup` to set your password.

### 3. Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `NOTION_API_KEY` | Notion integration token |
| `NOTION_TASKS_DB` | Notion Tasks database ID |
| `NOTION_PROJECTS_DB` | Notion Projects database ID |
| `OPENCLAW_GATEWAY_URL` | OpenClaw gateway URL (default: `http://localhost:18789`) |
| `OPENCLAW_GATEWAY_TOKEN` | OpenClaw gateway auth token |
| `OPENCLAW_WORKSPACE` | Path to `.openclaw/workspace` directory |
| `DATA_DIR` | Where dashboard data is stored (default: `./data`) |

## Agent API

Agents interact with the dashboard via a separate API-key authenticated endpoint:

```
Base URL: http://localhost:18790/api/v1/agent
Auth: X-API-Key: <ingest_api_key>
```

| Endpoint | Description |
|----------|-------------|
| `GET /tasks` | List tasks |
| `POST /tasks` | Create task |
| `PATCH /tasks/{id}` | Update task |
| `GET /sessions` | List sessions |
| `GET /comments?routed_to={agent_id}` | Get pending comments |
| `PATCH /comments/{id}/deliver` | Mark comment as delivered |

## OpenClaw Hook Config

Add to `openclaw.json` to stream events to the dashboard:

```json
{
  "hooks": {
    "internal": {
      "entries": {
        "dashboard-event-sink": {
          "type": "http-webhook",
          "url": "http://localhost:18790/api/v1/events/ingest",
          "headers": { "X-API-Key": "<ingest_api_key>" },
          "events": ["session.start", "session.end", "command.execute", "agent.delegate", "memory.write", "error"]
        }
      }
    }
  }
}
```

## Project Structure

```
edith-ops/
├── backend/
│   └── app/
│       ├── api/v1/        # REST endpoints
│       ├── ws/            # WebSocket hub
│       ├── core/          # Auth, event bus, deps
│       ├── domain/        # Pydantic models
│       ├── storage/       # JSON repositories
│       └── services/      # Business logic, file watcher, Notion sync
├── frontend/
│   └── src/
│       ├── pages/         # One per navigation item
│       ├── components/    # UI components
│       ├── api/           # API call modules
│       ├── stores/        # Zustand stores
│       └── hooks/         # useWebSocket, etc.
└── data/                  # Runtime data (gitignored)
```
