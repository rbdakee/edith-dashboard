"""
Filesystem watcher for OpenClaw workspace and logs.
Watches:
  - {openclaw_dir}/logs/commands.log  — session events (every Telegram message)
  - {workspace}/memory/               — memory files written by agents
  - {workspace}/agents/               — agent context files
  - {workspace}/                      — root workspace files
"""
import json
import re
import asyncio
from pathlib import Path
from datetime import datetime, timezone

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

_observer: Observer | None = None
_loop = None

# Track last known size of commands.log so we only parse new lines
_commands_log_offset: int = 0

# In-memory snapshots for file diff computation: path → last known content
_file_snapshots: dict[str, str] = {}

# If a session file has no .lock and has been quiet for this long, treat as finished.
_SESSION_STALE_SECONDS = 30


def _parse_session_key(session_key: str) -> str | None:
    """Extract agent_id from sessionKey like 'agent:main:telegram:direct:893220231'."""
    parts = session_key.split(":")
    if len(parts) >= 2 and parts[0] == "agent":
        return parts[1]
    return None


class WorkspaceEventHandler(FileSystemEventHandler):
    def __init__(self, bus, loop):
        super().__init__()
        self.bus = bus
        self.loop = loop

    def _emit(self, event_data: dict):
        """Schedule coroutine in the FastAPI event loop from watchdog thread."""
        async def _publish_and_store(data: dict):
            from app.storage.event_repo import event_repo
            from app.domain.models import Event
            try:
                event = Event(**data)
                await event_repo.append(event)
            except Exception as e:
                print(f"[file_watcher] store error: {e}")
            await self.bus.publish(data)

        try:
            asyncio.run_coroutine_threadsafe(_publish_and_store(event_data), self.loop)
        except Exception as e:
            print(f"[file_watcher] _emit error: {e}")

    def _handle_session_file(self, path: str, agent_id: str, event_type: str):
        """Handle new/modified session JSONL file from .openclaw/agents/{agent}/sessions/."""
        p = Path(path)
        # Extract session UUID from filename (ignore .deleted/.reset suffixes)
        stem = p.name.split(".jsonl")[0]
        openclaw_session_id = stem

        is_new = event_type == "file.created"
        is_deleted = ".deleted" in p.name or ".reset" in p.name

        if is_deleted:
            etype = "session.completed"
        elif is_new:
            etype = "session.started"
        else:
            # Heuristic for sessions that finish without .deleted/.reset rename:
            # if .jsonl has no lock and hasn't changed for a short grace period,
            # mark it as completed.
            lock_path = p.with_name(f"{openclaw_session_id}.jsonl.lock")
            try:
                age_seconds = (datetime.now(timezone.utc) - datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)).total_seconds()
            except Exception:
                age_seconds = 0
            if (not lock_path.exists()) and age_seconds >= _SESSION_STALE_SECONDS:
                etype = "session.completed"
            else:
                return  # ignore plain modifications while session is active

        title = f"Session {etype.split('.')[1]}: {agent_id}"
        print(f"[file_watcher] {etype}: agent={agent_id} session={openclaw_session_id}")

        self._emit({
            "id": f"evt_sess_{datetime.now(timezone.utc).timestamp():.6f}".replace(".", "_"),
            "type": etype,
            "agent_id": agent_id,
            "source": "watcher",
            "title": title,
            "data": {"session_id": openclaw_session_id, "path": path},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if is_new:
            self._update_agent(agent_id, "active")
            self._create_session(agent_id, openclaw_session_id, datetime.now(timezone.utc).isoformat(), "openclaw")
        elif etype == "session.completed":
            self._update_agent(agent_id, "idle")
            self._complete_session(openclaw_session_id)

    def _register_artifact(self, path: str):
        async def _do():
            from app.storage.artifact_repo import artifact_repo
            from app.domain.models import Artifact
            p = Path(path)
            try:
                size = p.stat().st_size
                preview = p.read_text(encoding="utf-8", errors="ignore")[:500]
            except Exception:
                return
            existing = await artifact_repo.list()
            for a in existing:
                if a.filepath == str(p):
                    return  # already registered
            artifact = Artifact(
                filename=p.name,
                filepath=str(p),
                mime_type="text/markdown",
                size=size,
                content_preview=preview,
            )
            await artifact_repo.create(artifact)
        try:
            asyncio.run_coroutine_threadsafe(_do(), self.loop)
        except Exception:
            pass

    def _create_session(self, agent_id: str, session_key: str, ts: str, source: str):
        async def _do():
            from app.storage.session_repo import session_repo
            from app.domain.models import Session
            session = Session(
                agent_id=agent_id,
                openclaw_session_id=session_key,
                status="active",
                started_at=ts,
                context_snapshot={"source": source, "session_key": session_key},
            )
            await session_repo.create(session)
        try:
            asyncio.run_coroutine_threadsafe(_do(), self.loop)
        except Exception:
            pass

    def _complete_session(self, openclaw_session_id: str):
        """Mark a session as completed in the session repo."""
        async def _do():
            from app.storage.session_repo import session_repo
            session = await session_repo.find_by_openclaw_id(openclaw_session_id)
            if session:
                await session_repo.update(session.id, {
                    "status": "completed",
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                })
        try:
            asyncio.run_coroutine_threadsafe(_do(), self.loop)
        except Exception:
            pass

    def _update_agent(self, agent_id: str, status: str = "active"):
        async def _do():
            from app.storage.agent_repo import agent_repo
            await agent_repo.update(agent_id, {
                "last_active_at": datetime.now(timezone.utc).isoformat(),
                "status": status,
            })
        try:
            asyncio.run_coroutine_threadsafe(_do(), self.loop)
        except Exception:
            pass

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle_file_change(event.src_path, "file.created")

    def on_modified(self, event):
        if event.is_directory:
            return
        self._handle_file_change(event.src_path, "file.updated")

    def _handle_commands_log(self, path: str):
        """Parse new lines appended to commands.log."""
        global _commands_log_offset
        p = Path(path)
        try:
            size = p.stat().st_size
            if size <= _commands_log_offset:
                return
            with open(p, "r", encoding="utf-8") as f:
                f.seek(_commands_log_offset)
                new_content = f.read()
            _commands_log_offset = size

            for line in new_content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue

                action = record.get("action", "")
                session_key = record.get("sessionKey", "")
                ts = record.get("timestamp", datetime.now(timezone.utc).isoformat())
                source = record.get("source", "")
                agent_id = _parse_session_key(session_key)

                if action in ("new", "reset", "resume"):
                    etype = "session.started" if action == "new" else "session.completed"
                    title = f"Session {action}: {session_key}"
                    print(f"[file_watcher] {etype}: agent={agent_id} source={source}")

                    event_id = f"evt_cmd_{datetime.now(timezone.utc).timestamp():.6f}".replace(".", "_")
                    self._emit({
                        "id": event_id,
                        "type": etype,
                        "agent_id": agent_id,
                        "source": "watcher",
                        "title": title,
                        "data": {
                            "session_key": session_key,
                            "action": action,
                            "sender_id": record.get("senderId"),
                            "channel": source,
                        },
                        "timestamp": ts,
                    })

                    if agent_id:
                        if action == "new":
                            self._update_agent(agent_id, "active")
                            self._create_session(agent_id, session_key, ts, source)
                        elif action in ("reset", "resume"):
                            self._update_agent(agent_id, "idle")
                            self._complete_session(session_key)

        except Exception as e:
            print(f"[file_watcher] commands.log parse error: {e}")

    def _handle_file_change(self, path: str, event_type: str):
        p = Path(path)
        name = p.name

        # commands.log — parse for session events
        if name == "commands.log":
            self._handle_commands_log(path)
            return

        if p.suffix not in (".md", ".json", ".jsonl"):
            return

        # Session JSONL files from .openclaw/agents/{agent}/sessions/
        if p.suffix == ".jsonl" and p.parent.name == "sessions":
            agent_id = p.parent.parent.name  # agents/{agent_id}/sessions/
            self._handle_session_file(path, agent_id, event_type)
            return

        parent = p.parent.name

        if parent == "memory" or re.match(r"\d{4}-\d{2}-\d{2}", name):
            etype = "memory.updated"
            title = f"Memory updated: {name}"
            agent_id = "main"
        elif name.startswith("task-") and name.endswith(".md"):
            etype = "memory.updated"
            title = f"Task log: {name}"
            agent_id = "main"
        else:
            etype = event_type
            title = f"File {event_type.split('.')[1]}: {name}"
            agent_id = None

        print(f"[file_watcher] {etype}: {path}")

        # Build event data — include diff for text files
        event_data_payload: dict = {"path": path}
        if p.suffix in (".md", ".json", ".txt", ".py") and event_type == "file.updated":
            try:
                current = p.read_text(encoding="utf-8", errors="ignore")[:6000]
                prev = _file_snapshots.get(path)
                if prev is not None:
                    import difflib
                    diff_lines = list(difflib.unified_diff(
                        prev.splitlines(), current.splitlines(),
                        lineterm="", n=2
                    ))
                    if diff_lines:
                        event_data_payload["diff"] = "\n".join(diff_lines[:120])
                else:
                    event_data_payload["content_snapshot"] = current[:2000]
                _file_snapshots[path] = current
            except Exception:
                pass

        self._emit({
            "id": f"evt_watcher_{datetime.now(timezone.utc).timestamp():.6f}".replace(".", "_"),
            "type": etype,
            "agent_id": agent_id,
            "source": "watcher",
            "title": title,
            "data": event_data_payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if agent_id:
            self._update_agent(agent_id)

        # Register .md files as artifacts
        if p.suffix == ".md" and p.exists():
            self._register_artifact(path)


def _reconcile_stale_active_sessions(openclaw_dir: str, loop):
    """One-shot reconciliation on startup against real OpenClaw lock/session truth."""

    async def _do():
        from app.services.openclaw_session_truth import reconcile_sessions_with_openclaw_truth

        try:
            stats = await reconcile_sessions_with_openclaw_truth(
                openclaw_dir=openclaw_dir,
                stale_seconds=_SESSION_STALE_SECONDS,
            )
            print(f"[file_watcher] startup reconcile: {stats}")
        except Exception as e:
            print(f"[file_watcher] startup reconcile error: {e}")

    try:
        asyncio.run_coroutine_threadsafe(_do(), loop)
    except Exception:
        pass


def start_file_watcher(event_bus, workspace_path: str, openclaw_dir: str = None, loop=None):
    """Start the watchdog observer."""
    global _observer, _loop, _commands_log_offset

    _loop = loop
    if _loop is None:
        try:
            _loop = asyncio.get_running_loop()
        except RuntimeError:
            _loop = asyncio.get_event_loop()

    # Initialize commands.log offset to current size (skip historical entries)
    if openclaw_dir:
        commands_log = Path(openclaw_dir) / "logs" / "commands.log"
        if commands_log.exists():
            _commands_log_offset = commands_log.stat().st_size
            print(f"[file_watcher] commands.log offset initialized at {_commands_log_offset} bytes")

    paths_to_watch = []
    if openclaw_dir:
        logs_dir = Path(openclaw_dir) / "logs"
        if logs_dir.exists():
            paths_to_watch.append(logs_dir)

        # Watch each agent's sessions directory
        agents_dir = Path(openclaw_dir) / "agents"
        if agents_dir.exists():
            for agent_sessions in agents_dir.glob("*/sessions"):
                if agent_sessions.is_dir():
                    paths_to_watch.append(agent_sessions)

    workspace = Path(workspace_path)
    for sub in ["memory", "agents", ""]:
        p = workspace / sub if sub else workspace
        if p.exists():
            paths_to_watch.append(p)

    handler = WorkspaceEventHandler(event_bus, _loop)
    _observer = Observer()

    watched = []
    seen = set()
    for watch_path in paths_to_watch:
        key = str(watch_path.resolve())
        if key in seen:
            continue
        seen.add(key)
        _observer.schedule(handler, str(watch_path), recursive=False)
        watched.append(str(watch_path))

    print(f"[file_watcher] Watching: {watched}")
    print(f"[file_watcher] Using loop: {_loop}")

    try:
        _observer.start()
        print("[file_watcher] Observer started.")
    except Exception as e:
        print(f"[file_watcher] Could not start observer: {e}")

    if openclaw_dir:
        _reconcile_stale_active_sessions(openclaw_dir, _loop)


def stop_file_watcher():
    global _observer
    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join()
    _observer = None
