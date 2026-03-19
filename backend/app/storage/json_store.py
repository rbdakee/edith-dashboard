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
    path.parent.mkdir(parents=True, exist_ok=True)
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
