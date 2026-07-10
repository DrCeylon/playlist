from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from playlist_builder.app.playlist_library.serialization import (
    SCHEMA_VERSION,
    playlist_detail_from_dict,
    playlist_detail_to_dict,
)
from playlist_builder.infrastructure.atomic_json import locked_json_document
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail


class JsonManagedPlaylistRepository:
    def __init__(self, path: Path = Path("data/playlists/managed_playlists.json")) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def list_playlists(self) -> list[ManagedPlaylistDetail]:
        payload = self._read_payload()
        records = self._records_from_payload(payload)
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
        def mutate(playlists: list[ManagedPlaylistDetail]) -> list[ManagedPlaylistDetail]:
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
            return updated

        self._mutate_playlists(mutate)
        return detail

    def delete(self, local_playlist_id: str) -> bool:
        removed = False

        def mutate(playlists: list[ManagedPlaylistDetail]) -> list[ManagedPlaylistDetail]:
            nonlocal removed
            kept = [item for item in playlists if item.summary.local_playlist_id != local_playlist_id]
            removed = len(kept) != len(playlists)
            return kept

        self._mutate_playlists(mutate)
        return removed

    def _records_from_payload(self, payload: dict[str, object]) -> list[ManagedPlaylistDetail]:
        playlists_raw = payload.get("playlists", [])
        if not isinstance(playlists_raw, list):
            return []
        records: list[ManagedPlaylistDetail] = []
        for item in playlists_raw:
            if isinstance(item, dict):
                records.append(playlist_detail_from_dict(item))
        return records

    def _mutate_playlists(
        self,
        mutator: Callable[[list[ManagedPlaylistDetail]], list[ManagedPlaylistDetail]],
    ) -> None:
        with locked_json_document(self._path) as locked:
            payload = self._normalize_payload(locked)
            updated = mutator(self._records_from_payload(payload))
            locked.clear()
            locked.update(
                {
                    "schema_version": SCHEMA_VERSION,
                    "playlists": [playlist_detail_to_dict(item) for item in updated],
                }
            )

    def _read_payload(self) -> dict[str, object]:
        if not self._path.exists():
            return {"schema_version": SCHEMA_VERSION, "playlists": []}
        try:
            with locked_json_document(self._path) as payload:
                return dict(self._normalize_payload(payload))
        except OSError:
            return {"schema_version": SCHEMA_VERSION, "playlists": []}

    def _normalize_payload(self, payload: dict[str, object]) -> dict[str, object]:
        version = int(payload.get("schema_version", SCHEMA_VERSION) or SCHEMA_VERSION)
        if version > SCHEMA_VERSION:
            return {"schema_version": SCHEMA_VERSION, "playlists": []}
        payload.setdefault("schema_version", SCHEMA_VERSION)
        payload.setdefault("playlists", [])
        return payload
