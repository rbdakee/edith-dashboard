from enum import Enum


class TaskStatus(str, Enum):
    idea = "idea"
    planned = "planned"
    in_progress = "in_progress"
    done = "done"
    archive = "archive"


class SubStatus(str, Enum):
    working = "working"
    thinking = "thinking"
    blocked = "blocked"
    waiting = "waiting"
    delegated = "delegated"
    reviewing = "reviewing"
    updating = "updating"


class Priority(str, Enum):
    p0 = "p0"
    p1 = "p1"
    p2 = "p2"
    p3 = "p3"


class AgentStatus(str, Enum):
    idle = "idle"
    active = "active"
    busy = "busy"


class SessionStatus(str, Enum):
    active = "active"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class EventSource(str, Enum):
    hook = "hook"
    watcher = "watcher"
    gateway = "gateway"
    user = "user"
    system = "system"


class CommentAuthor(str, Enum):
    user = "user"
    edith_main = "edith-main"
    edith_dev = "edith-dev"
    edith_routine = "edith-routine"
    edith_analytics = "edith-analytics"
    system = "system"


class EventType(str, Enum):
    # task events
    task_created = "task.created"
    task_status_changed = "task.status_changed"
    task_plan_updated = "task.plan_updated"
    task_context_updated = "task.context_updated"
    task_approved = "task.approved"
    task_assigned = "task.assigned"
    task_comment_added = "task.comment_added"
    task_subtask_created = "task.subtask_created"
    # session events
    session_started = "session.started"
    session_completed = "session.completed"
    session_failed = "session.failed"
    session_context_loaded = "session.context_loaded"
    # agent events
    agent_status_changed = "agent.status_changed"
    agent_delegation_sent = "agent.delegation_sent"
    agent_delegation_received = "agent.delegation_received"
    agent_error = "agent.error"
    # code events
    code_written = "code.written"
    code_committed = "code.committed"
    code_tested = "code.tested"
    # memory events
    memory_updated = "memory.updated"
    memory_read = "memory.read"
    # file events
    file_created = "file.created"
    file_updated = "file.updated"
    file_deleted = "file.deleted"
    # comment events
    comment_created = "comment.created"
    comment_delivered = "comment.delivered"
    comment_read = "comment.read"
    # system events
    system_hook_received = "system.hook_received"
    system_sync_notion = "system.sync_notion"
    system_cron_executed = "system.cron_executed"
    system_error = "system.error"


class ProjectStatus(str, Enum):
    active = "Active"
    on_hold = "On Hold"
    completed = "Completed"
    archived = "Archived"
