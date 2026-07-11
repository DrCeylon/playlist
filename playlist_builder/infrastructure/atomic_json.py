from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


@contextmanager
def advisory_file_lock(lock_path: Path) -> Iterator[None]:
    """Exclusive advisory lock — portable on macOS and Linux (fcntl)."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield


def replace_file_atomic(target: Path, content: str) -> None:
    """Publish a file atomically via temp + os.replace (POSIX).

    Readers never observe a partial file at ``target``: either the previous
    revision remains or the new revision appears in full.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(f"{target.suffix}.tmp")
    try:
        temp.write_text(content, encoding="utf-8")
        os.replace(temp, target)
    finally:
        if temp.exists():
            try:
                temp.unlink()
            except OSError:
                pass


@contextmanager
def locked_json_document(path: Path) -> Iterator[dict[str, Any]]:
    """Read-modify-write a JSON object file under an exclusive advisory lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        raw = handle.read()
        payload: dict[str, Any]
        if raw.strip():
            try:
                loaded = json.loads(raw)
            except json.JSONDecodeError:
                loaded = {}
        else:
            loaded = {}
        if not isinstance(loaded, dict):
            loaded = {}
        yield loaded
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps(loaded, indent=2, ensure_ascii=False))
        handle.flush()


