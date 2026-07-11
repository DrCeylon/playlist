from __future__ import annotations

import json
from pathlib import Path

from playlist_builder.app.playlist_library.errors import UnsupportedSchemaVersionError
from playlist_builder.app.playlist_sync_operations.serialization import (
    SCHEMA_VERSION,
    operation_from_dict,
    operation_to_dict,
)
from playlist_builder.infrastructure.atomic_json import locked_json_document
from playlist_builder.ui.shared.dto.playlist_sync import PlaylistSyncOperation


class JsonPlaylistSyncOperationRepository:
    def __init__(self, path: Path = Path("data/playlists/sync_operations.json")) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def list_operations(self) -> list[PlaylistSyncOperation]:
        payload = self._read_payload()
        records = self._records_from_payload(payload)
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
        def mutate(operations: list[PlaylistSyncOperation]) -> list[PlaylistSyncOperation]:
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
            return updated

        self._mutate_operations(mutate)
        return operation

    def _records_from_payload(self, payload: dict[str, object]) -> list[PlaylistSyncOperation]:
        operations_raw = payload.get("operations", [])
        if not isinstance(operations_raw, list):
            return []
        return [operation_from_dict(item) for item in operations_raw if isinstance(item, dict)]

    def _mutate_operations(
        self,
        mutator,
    ) -> None:
        with locked_json_document(self._path) as locked:
            payload = self._normalize_payload(locked)
            updated = mutator(self._records_from_payload(payload))
            locked.clear()
            locked.update(
                {
                    "schema_version": SCHEMA_VERSION,
                    "operations": [operation_to_dict(item) for item in updated],
                }
            )

    def _read_payload(self) -> dict[str, object]:
        if not self._path.exists():
            return {"schema_version": SCHEMA_VERSION, "operations": []}
        try:
            with locked_json_document(self._path) as payload:
                return dict(self._normalize_payload(payload))
        except OSError:
            return {"schema_version": SCHEMA_VERSION, "operations": []}

    def _normalize_payload(self, payload: dict[str, object]) -> dict[str, object]:
        version = int(payload.get("schema_version", SCHEMA_VERSION) or SCHEMA_VERSION)
        if version > SCHEMA_VERSION:
            raise UnsupportedSchemaVersionError(version, SCHEMA_VERSION, str(self._path))
        payload.setdefault("schema_version", SCHEMA_VERSION)
        payload.setdefault("operations", [])
        return payload
