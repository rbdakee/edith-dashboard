from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.enums import (
    TaskStatus, SubStatus, Priority, AgentStatus,
    SessionStatus, EventSource, CommentAuthor, ProjectStatus,
)


def _uuid() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Task ──────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.idea
    sub_status: SubStatus | None = None
    priority: Priority = Priority.p2
    category: str = "work"
    project_id: str | None = None
    executor_agent: str | None = None
    plan: str | None = None
    context_file: str | None = None
    parent_task_id: str | None = None
    notion_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    sub_status: SubStatus | None = None
    priority: Priority | None = None
    category: str | None = None
    project_id: str | None = None
    executor_agent: str | None = None
    plan: str | None = None
    context_file: str | None = None
    parent_task_id: str | None = None
    notion_id: str | None = None
    approved: bool | None = None


class Task(BaseModel):
    id: str = Field(default_factory=lambda: f"tsk_{uuid4().hex[:12]}")
    notion_id: str | None = None
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.idea
    sub_status: SubStatus | None = None
    priority: Priority = Priority.p2
    category: str = "work"
    project_id: str | None = None
    executor_agent: str | None = None
    plan: str | None = None
    context_file: str | None = None
    parent_task_id: str | None = None
    approved: bool = False
    approved_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    last_activity_at: datetime = Field(default_factory=_now)
    last_status_change_at: datetime = Field(default_factory=_now)


# ── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.active
    deadline: str | None = None
    notion_id: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    deadline: str | None = None
    notion_id: str | None = None


class Project(BaseModel):
    id: str = Field(default_factory=lambda: f"prj_{uuid4().hex[:12]}")
    title: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.active
    deadline: str | None = None
    notion_id: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ── Event ─────────────────────────────────────────────────────────────────────

class Event(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:12]}")
    type: str
    task_id: str | None = None
    session_id: str | None = None
    agent_id: str | None = None
    source: EventSource = EventSource.system
    title: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_now)


# ── Session ───────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    agent_id: str
    task_id: str | None = None
    openclaw_session_id: str | None = None
    model: str = ""


class SessionUpdate(BaseModel):
    status: SessionStatus | None = None
    ended_at: datetime | None = None
    context_snapshot: dict[str, Any] | None = None
    prompts: list[dict[str, Any]] | None = None
    actions: list[dict[str, Any]] | None = None
    outputs: list[dict[str, Any]] | None = None


class Session(BaseModel):
    id: str = Field(default_factory=lambda: f"ses_{uuid4().hex[:12]}")
    openclaw_session_id: str | None = None
    agent_id: str
    task_id: str | None = None
    status: SessionStatus = SessionStatus.active
    started_at: datetime = Field(default_factory=_now)
    ended_at: datetime | None = None
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    prompts: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    outputs: list[dict[str, Any]] = Field(default_factory=list)
    model: str = ""


# ── Agent ─────────────────────────────────────────────────────────────────────

class AgentUpdate(BaseModel):
    status: AgentStatus | None = None
    current_task_id: str | None = None
    current_session_id: str | None = None
    last_active_at: datetime | None = None


class Agent(BaseModel):
    id: str
    name: str
    model: str
    status: AgentStatus = AgentStatus.idle
    current_task_id: str | None = None
    current_session_id: str | None = None
    skills: list[str] = Field(default_factory=list)
    last_active_at: datetime | None = None


# ── Artifact ──────────────────────────────────────────────────────────────────

class ArtifactCreate(BaseModel):
    task_id: str | None = None
    session_id: str | None = None
    filename: str
    filepath: str
    mime_type: str = "text/plain"
    size: int = 0
    content_preview: str | None = None


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: f"art_{uuid4().hex[:12]}")
    task_id: str | None = None
    session_id: str | None = None
    filename: str
    filepath: str
    mime_type: str = "text/plain"
    size: int = 0
    content_preview: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ── Comment ───────────────────────────────────────────────────────────────────

class FragmentRef(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    text_selection: str = ""


class CommentCreate(BaseModel):
    task_id: str | None = None
    artifact_id: str | None = None
    session_id: str | None = None
    author: CommentAuthor = CommentAuthor.user
    content: str
    fragment_refs: list[FragmentRef] = Field(default_factory=list)
    routed_to: str | None = None


class Comment(BaseModel):
    id: str = Field(default_factory=lambda: f"cmt_{uuid4().hex[:12]}")
    task_id: str | None = None
    artifact_id: str | None = None
    session_id: str | None = None
    author: CommentAuthor = CommentAuthor.user
    content: str
    fragment_refs: list[FragmentRef] = Field(default_factory=list)
    routed_to: str | None = None
    delivered: bool = False
    delivered_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)


# ── Settings ──────────────────────────────────────────────────────────────────

class AppSettings(BaseModel):
    notion_sync_enabled: bool = False
    notion_sync_interval_seconds: int = 60
    gateway_poll_interval_seconds: int = 10
    notifications_enabled: bool = True
    theme: str = "dark"
    updated_at: datetime = Field(default_factory=_now)
