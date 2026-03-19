"""
File browser/content API — serves real filesystem directories/files from allowed roots.
Used by the frontend Files page as a real file manager (folders first).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Depends

from app.core.deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/files", tags=["files"])


def _allowed_prefixes() -> list[Path]:
    """Canonical allowed roots for file browser/content access."""
    prefixes: list[Path] = []

    if settings.openclaw_workspace:
        prefixes.append(Path(settings.openclaw_workspace).resolve())
    if settings.openclaw_dir:
        prefixes.append(Path(settings.openclaw_dir).resolve())

    # Dashboard runtime data (artifacts, events, etc.)
    data_root = Path(settings.data_dir).resolve()
    prefixes.append(data_root)

    # De-duplicate while preserving order
    unique: list[Path] = []
    seen: set[str] = set()
    for p in prefixes:
        key = str(p).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


def _is_allowed(path: Path) -> bool:
    resolved = path.resolve()
    for prefix in _allowed_prefixes():
        try:
            resolved.relative_to(prefix)
            return True
        except ValueError:
            continue
    return False


def _guess_mime(p: Path) -> str:
    ext = p.suffix.lower()
    mime_map = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".py": "text/x-python",
        ".ts": "text/typescript",
        ".tsx": "text/typescript",
        ".js": "text/javascript",
        ".json": "application/json",
        ".yaml": "text/yaml",
        ".yml": "text/yaml",
        ".toml": "text/toml",
        ".html": "text/html",
        ".css": "text/css",
    }
    return mime_map.get(ext, "text/plain")


@router.get("/roots")
async def list_roots(_user: str = Depends(get_current_user)):
    roots = [str(p) for p in _allowed_prefixes() if p.exists()]
    return {"roots": roots}


@router.get("/list")
async def list_directory(
    path: str | None = Query(None, description="Directory path to list. Defaults to first allowed root."),
    _user: str = Depends(get_current_user),
):
    roots = [p for p in _allowed_prefixes() if p.exists()]
    if not roots:
        return {"path": None, "parent": None, "entries": [], "roots": []}

    if path:
        current = Path(path)
    else:
        current = roots[0]

    if not _is_allowed(current):
        raise HTTPException(403, "Access to this path is not allowed")

    if not current.exists():
        raise HTTPException(404, "Directory not found")

    if not current.is_dir():
        raise HTTPException(400, "Path is not a directory")

    entries: list[dict] = []
    try:
        for child in current.iterdir():
            is_dir = child.is_dir()
            size = None if is_dir else child.stat().st_size
            entries.append({
                "name": child.name,
                "path": str(child.resolve()),
                "is_dir": is_dir,
                "size": size,
                "mime_type": None if is_dir else _guess_mime(child),
            })
    except PermissionError:
        raise HTTPException(403, "Permission denied")

    # Folders first, then files; then alphabetical (case-insensitive)
    entries.sort(key=lambda e: (not e["is_dir"], str(e["name"]).lower()))

    parent = current.parent
    parent_path = str(parent) if parent != current and _is_allowed(parent) else None

    return {
        "path": str(current.resolve()),
        "parent": parent_path,
        "entries": entries,
        "roots": [str(p) for p in roots],
    }


@router.get("/content")
async def get_file_content(
    path: str = Query(..., description="Absolute path to the file"),
    _user: str = Depends(get_current_user),
):
    """Read and return the content of a file. Only files in allowed directories."""
    p = Path(path)

    if not _is_allowed(p):
        raise HTTPException(403, "Access to this path is not allowed")

    if not p.exists():
        raise HTTPException(404, "File not found")

    if not p.is_file():
        raise HTTPException(400, "Path is not a file")

    # Limit file size to 1MB
    size = p.stat().st_size
    if size > 1_048_576:
        raise HTTPException(413, "File too large (max 1MB)")

    content = p.read_text(encoding="utf-8", errors="replace")

    return {
        "content": content,
        "path": str(p),
        "filename": p.name,
        "size": size,
        "mime_type": _guess_mime(p),
    }
