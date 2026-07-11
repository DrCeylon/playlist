from __future__ import annotations

from pathlib import Path

from playlist_builder.infrastructure.atomic_json import locked_json_document
from playlist_builder.ui.shared.history.errors import UnsupportedSchemaVersionError
from playlist_builder.ui.shared.history.models import SessionHistoryRecord
from playlist_builder.ui.shared.history.serialization import SCHEMA_VERSION, record_from_dict, record_to_dict


class SessionHistoryRepository:
    def __init__(self, path: Path = Path("data/history/sessions.json")) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def list_sessions(self) -> list[SessionHistoryRecord]:
        payload = self._read_payload()
        records = self._records_from_payload(payload)
        records.sort(key=lambda item: item.started_at_iso, reverse=True)
        return records

    def get_session(self, session_id: str) -> SessionHistoryRecord | None:
        for item in self.list_sessions():
            if item.session_id == session_id:
                return item
        return None

    def upsert(self, record: SessionHistoryRecord) -> SessionHistoryRecord:
        def mutate(sessions: list[SessionHistoryRecord]) -> list[SessionHistoryRecord]:
            replaced = False
            updated: list[SessionHistoryRecord] = []
            for item in sessions:
                if item.session_id == record.session_id:
                    updated.append(record)
                    replaced = True
                else:
                    updated.append(item)
            if not replaced:
                updated.append(record)
            return updated

        self._mutate_sessions(mutate)
        return record

    def delete_session(self, session_id: str) -> bool:
        if not any(item.session_id == session_id for item in self.list_sessions()):
            return False

        def mutate(sessions: list[SessionHistoryRecord]) -> list[SessionHistoryRecord]:
            return [item for item in sessions if item.session_id != session_id]

        self._mutate_sessions(mutate)
        return True

    def clear(self) -> None:
        self._mutate_sessions(lambda _sessions: [])

    def _records_from_payload(self, payload: dict[str, object]) -> list[SessionHistoryRecord]:
        sessions_raw = payload.get("sessions", [])
        if not isinstance(sessions_raw, list):
            return []
        return [record_from_dict(item) for item in sessions_raw if isinstance(item, dict)]

    def _mutate_sessions(self, mutator) -> None:
        with locked_json_document(self._path) as locked:
            payload = self._normalize_payload(locked)
            updated = mutator(self._records_from_payload(payload))
            locked.clear()
            locked.update(
                {
                    "schema_version": SCHEMA_VERSION,
                    "sessions": [record_to_dict(item) for item in updated],
                }
            )

    def _read_payload(self) -> dict[str, object]:
        if not self._path.exists():
            return {"schema_version": SCHEMA_VERSION, "sessions": []}
        try:
            with locked_json_document(self._path) as payload:
                return dict(self._normalize_payload(payload))
        except OSError:
            return {"schema_version": SCHEMA_VERSION, "sessions": []}

    def _normalize_payload(self, payload: dict[str, object]) -> dict[str, object]:
        version = int(payload.get("schema_version", SCHEMA_VERSION) or SCHEMA_VERSION)
        if version > SCHEMA_VERSION:
            raise UnsupportedSchemaVersionError(version, SCHEMA_VERSION, str(self._path))
        payload.setdefault("schema_version", SCHEMA_VERSION)
        payload.setdefault("sessions", [])
        return payload
