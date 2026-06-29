from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Self


class JsonCache:
    """JSON-backed key-value store with lazy persistence."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._dirty = False
        if self.path.exists():
            self._data: dict[str, Any] = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self._data = {}

    def get(self, key: str) -> Any | None:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._dirty = True

    def set_many(self, entries: dict[str, Any]) -> None:
        self._data.update(entries)
        self._dirty = True

    def delete(self, key: str) -> bool:
        if key not in self._data:
            return False
        del self._data[key]
        self._dirty = True
        return True

    def flush(self) -> None:
        if not self._dirty:
            return
        self.save()
        self._dirty = False

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._dirty = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.flush()
