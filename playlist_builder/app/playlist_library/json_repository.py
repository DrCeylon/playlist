from __future__ import annotations

import json
from pathlib import Path

from playlist_builder.app.playlist_library.serialization import (
    SCHEMA_VERSION,
    playlist_detail_from_dict,
    playlist_detail_to_dict,
)
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail


class JsonManagedPlaylistRepository:
    def __init__(self, path: Path = Path("data/playlists/managed_playlists.json")) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def list_playlists(self) -> list[ManagedPlaylistDetail]:
        payload = self._read_payload()
        playlists_raw = payload.get("playlists", [])
        if not isinstance(playlists_raw, list):
            return []
        records: list[ManagedPlaylistDetail] = []
        for item in playlists_raw:
            if isinstance(item, dict):
                records.append(playlist_detail_from_dict(item))
        records.sort(key=lambda item: item.summary.updated_at_iso or item.summary.created_at_iso, reverse=True)
        return records

    def get_playlist(self, local_playlist_id: str) -> ManagedPlaylistDetail | None:
        playlist_id = str(local_playlist_id).strip()
        if not playlist_id:
            return None
        for item in self.list_playlists():
            if item.summary.local_playlist_id == playlist_id:
                return item
        return None

    def upsert(self, detail: ManagedPlaylistDetail) -> ManagedPlaylistDetail:
        playlists = self.list_playlists()
        replaced = False
        updated: list[ManagedPlaylistDetail] = []
        for item in playlists:
            if item.summary.local_playlist_id == detail.summary.local_playlist_id:
                updated.append(detail)
                replaced = True
            else:
                updated.append(item)
        if not replaced:
            updated.append(detail)
        self._write_payload(updated)
        return detail

    def delete(self, local_playlist_id: str) -> bool:
        playlists = self.list_playlists()
        kept = [item for item in playlists if item.summary.local_playlist_id != local_playlist_id]
        if len(kept) == len(playlists):
            return False
        self._write_payload(kept)
        return True

    def _read_payload(self) -> dict[str, object]:
        if not self._path.exists():
            return {"schema_version": SCHEMA_VERSION, "playlists": []}
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": SCHEMA_VERSION, "playlists": []}
        if not isinstance(payload, dict):
            return {"schema_version": SCHEMA_VERSION, "playlists": []}
        version = int(payload.get("schema_version", SCHEMA_VERSION) or SCHEMA_VERSION)
        if version > SCHEMA_VERSION:
            return {"schema_version": SCHEMA_VERSION, "playlists": []}
        payload.setdefault("schema_version", SCHEMA_VERSION)
        payload.setdefault("playlists", [])
        return payload

    def _write_payload(self, playlists: list[ManagedPlaylistDetail]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "playlists": [playlist_detail_to_dict(item) for item in playlists],
        }
        temp = self._path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self._path)
