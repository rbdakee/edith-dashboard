"""
File content API — serve file contents from allowed directories.
Used by the frontend to display file contents in the dashboard.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from pathlib import Path

from app.core.deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/files", tags=["files"])

# Only files within these directories can be served
def _allowed_prefixes() -> list[Path]:
    prefixes = []
    if settings.openclaw_workspace:
        prefixes.append(Path(settings.openclaw_workspace).resolve())
    if settings.openclaw_dir:
        prefixes.append(Path(settings.openclaw_dir).resolve())
    return prefixes


def _is_allowed(path: Path) -> bool:
    resolved = path.resolve()
    for prefix in _allowed_prefixes():
        try:
            resolved.relative_to(prefix)
            return True
        except ValueError:
            continue
    return False


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
    mime_type = mime_map.get(ext, "text/plain")

    return {
        "content": content,
        "path": str(p),
        "filename": p.name,
        "size": size,
        "mime_type": mime_type,
    }
