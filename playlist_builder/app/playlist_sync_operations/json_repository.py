from __future__ import annotations

import json
from pathlib import Path

from playlist_builder.app.playlist_sync_operations.serialization import (
    SCHEMA_VERSION,
    operation_from_dict,
    operation_to_dict,
)
from playlist_builder.ui.shared.dto.playlist_sync import PlaylistSyncOperation


class JsonPlaylistSyncOperationRepository:
    def __init__(self, path: Path = Path("data/playlists/sync_operations.json")) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def list_operations(self) -> list[PlaylistSyncOperation]:
        payload = self._read_payload()
        operations_raw = payload.get("operations", [])
        if not isinstance(operations_raw, list):
            return []
        records = [operation_from_dict(item) for item in operations_raw if isinstance(item, dict)]
        records.sort(key=lambda item: item.created_at_iso, reverse=True)
        return records

    def get_operation(self, operation_id: str) -> PlaylistSyncOperation | None:
        operation_key = str(operation_id).strip()
        if not operation_key:
            return None
        for item in self.list_operations():
            if item.operation_id == operation_key:
                return item
        return None

    def get_by_idempotency_key(self, idempotency_key: str) -> PlaylistSyncOperation | None:
        key = str(idempotency_key).strip()
        if not key:
            return None
        for item in self.list_operations():
            if item.idempotency_key == key:
                return item
        return None

    def upsert(self, operation: PlaylistSyncOperation) -> PlaylistSyncOperation:
        operations = self.list_operations()
        replaced = False
        updated: list[PlaylistSyncOperation] = []
        for item in operations:
            if item.operation_id == operation.operation_id:
                updated.append(operation)
                replaced = True
            else:
                updated.append(item)
        if not replaced:
            updated.append(operation)
        self._write_payload(updated)
        return operation

    def _read_payload(self) -> dict[str, object]:
        if not self._path.exists():
            return {"schema_version": SCHEMA_VERSION, "operations": []}
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": SCHEMA_VERSION, "operations": []}
        if not isinstance(payload, dict):
            return {"schema_version": SCHEMA_VERSION, "operations": []}
        version = int(payload.get("schema_version", SCHEMA_VERSION) or SCHEMA_VERSION)
        if version > SCHEMA_VERSION:
            return {"schema_version": SCHEMA_VERSION, "operations": []}
        payload.setdefault("schema_version", SCHEMA_VERSION)
        payload.setdefault("operations", [])
        return payload

    def _write_payload(self, operations: list[PlaylistSyncOperation]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "operations": [operation_to_dict(item) for item in operations],
        }
        temp = self._path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self._path)
