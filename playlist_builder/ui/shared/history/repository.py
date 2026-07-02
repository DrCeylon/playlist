from __future__ import annotations

import json
from pathlib import Path

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
        sessions_raw = payload.get("sessions", [])
        if not isinstance(sessions_raw, list):
            return []
        records: list[SessionHistoryRecord] = []
        for item in sessions_raw:
            if isinstance(item, dict):
                records.append(record_from_dict(item))
        records.sort(key=lambda item: item.started_at_iso, reverse=True)
        return records

    def get_session(self, session_id: str) -> SessionHistoryRecord | None:
        for item in self.list_sessions():
            if item.session_id == session_id:
                return item
        return None

    def upsert(self, record: SessionHistoryRecord) -> SessionHistoryRecord:
        sessions = self.list_sessions()
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
        self._write_payload(updated)
        return record

    def delete_session(self, session_id: str) -> bool:
        sessions = self.list_sessions()
        kept = [item for item in sessions if item.session_id != session_id]
        if len(kept) == len(sessions):
            return False
        self._write_payload(kept)
        return True

    def clear(self) -> None:
        self._write_payload([])

    def _read_payload(self) -> dict[str, object]:
        if not self._path.exists():
            return {"schema_version": SCHEMA_VERSION, "sessions": []}
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": SCHEMA_VERSION, "sessions": []}
        if not isinstance(payload, dict):
            return {"schema_version": SCHEMA_VERSION, "sessions": []}
        version = int(payload.get("schema_version", SCHEMA_VERSION) or SCHEMA_VERSION)
        if version > SCHEMA_VERSION:
            return {"schema_version": SCHEMA_VERSION, "sessions": []}
        payload.setdefault("schema_version", SCHEMA_VERSION)
        payload.setdefault("sessions", [])
        return payload

    def _write_payload(self, sessions: list[SessionHistoryRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "sessions": [record_to_dict(item) for item in sessions],
        }
        temp = self._path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self._path)

