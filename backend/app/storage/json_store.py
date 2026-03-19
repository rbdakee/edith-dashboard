import json
import os
import time
import uuid
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
    """Atomically write JSON file (write to tmp, then rename).

    Windows can deny ``os.replace`` with WinError 5/32 while another
    process/thread briefly has the destination open for reading. Use a unique
    temp file, flush it to disk first, then retry the replace with backoff.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())

    last_err = None
    for attempt in range(6):
        try:
            os.replace(tmp, path)
            return
        except PermissionError as e:
            last_err = e
            # 10ms,20ms,40ms,80ms,160ms,320ms
            time.sleep(0.01 * (2 ** attempt))

    # Best-effort cleanup on persistent failure
    try:
        if tmp.exists():
            tmp.unlink()
    except Exception:
        pass
    raise last_err if last_err else RuntimeError(f"Failed to replace {path}")


def append_jsonl(path: Path, record: dict):
    """Append a single JSON record to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    """Read all records from a JSONL file.

    Be tolerant to malformed partial lines: event JSONL can occasionally contain
    a truncated/interleaved fragment from a past concurrent append. One bad line
    must not take down the whole events API or hide all valid records.
    """
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records
