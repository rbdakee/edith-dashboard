from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.domain.models import Task  # noqa: E402
from app.storage.task_repo import TaskRepository  # noqa: E402


def _seed_repo() -> TaskRepository:
    repo = TaskRepository()

    parent = Task(id="tsk_parent", title="Parent task")
    sibling = Task(id="tsk_sibling", title="Sibling task")
    child = Task(id="tsk_child", title="Child task", parent_task_id=parent.id)

    repo._loaded = True
    repo._index = {
        parent.id: repo._index_entry(parent),
        sibling.id: repo._index_entry(sibling),
        child.id: repo._index_entry(child),
    }
    repo._cache = {
        parent.id: parent.model_dump(mode="json"),
        sibling.id: sibling.model_dump(mode="json"),
        child.id: child.model_dump(mode="json"),
    }
    return repo


def test_list_top_level_only_excludes_subtasks() -> None:
    repo = _seed_repo()

    tasks = asyncio.run(repo.list(top_level_only=True))

    assert {task.id for task in tasks} == {"tsk_parent", "tsk_sibling"}


def test_list_by_parent_returns_only_matching_subtasks() -> None:
    repo = _seed_repo()

    tasks = asyncio.run(repo.list(parent_task_id="tsk_parent"))

    assert [task.id for task in tasks] == ["tsk_child"]


def test_list_with_include_semantics_can_return_mixed_hierarchy() -> None:
    repo = _seed_repo()

    tasks = asyncio.run(repo.list())

    assert {task.id for task in tasks} == {"tsk_parent", "tsk_sibling", "tsk_child"}
