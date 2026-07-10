from __future__ import annotations

import json
from pathlib import Path

from playlist_builder.ui.shared.dto.remote_playlist import (
    RemotePlaylistSnapshot,
    RemotePlaylistTrack,
    remote_playlist_snapshot_checksum,
)


def snapshot_id_from_checksum(checksum: str) -> str:
    return f"snap-{checksum}"


class SnapshotArchive:
    """Immutable remote snapshot store — checksum is the deduplication key."""

    def __init__(self, directory: Path = Path("data/playlists/snapshots")) -> None:
        self._directory = directory

    @property
    def directory(self) -> Path:
        return self._directory

    def store(self, snapshot: RemotePlaylistSnapshot) -> str:
        checksum = snapshot.checksum or remote_playlist_snapshot_checksum(snapshot.tracks)
        path = self._path_for_checksum(checksum)
        if path.exists():
            return checksum
        self._directory.mkdir(parents=True, exist_ok=True)
        payload = snapshot.to_dict()
        payload["checksum"] = checksum
        payload["snapshot_id"] = snapshot_id_from_checksum(checksum)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(path)
        return checksum

    def get(self, checksum: str) -> RemotePlaylistSnapshot | None:
        key = str(checksum).strip()
        if not key:
            return None
        path = self._path_for_checksum(key)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(raw, dict):
            return None
        return _snapshot_from_dict(raw)

    def _path_for_checksum(self, checksum: str) -> Path:
        safe = "".join(char for char in checksum if char.isalnum() or char in "-_")
        return self._directory / f"{safe}.json"


def _snapshot_from_dict(raw: dict[str, object]) -> RemotePlaylistSnapshot:
    from playlist_builder.canonical.enums import ProviderId

    tracks_raw = raw.get("tracks", [])
    tracks: list[RemotePlaylistTrack] = []
    if isinstance(tracks_raw, list):
        for item in tracks_raw:
            if not isinstance(item, dict):
                continue
            metadata = item.get("provider_metadata", {})
            tracks.append(
                RemotePlaylistTrack(
                    remote_track_id=str(item.get("remote_track_id", "")),
                    artist=str(item.get("artist", "")),
                    title=str(item.get("title", "")),
                    album=str(item.get("album", "")),
                    duration_ms=int(item.get("duration_ms", 0) or 0),
                    position=int(item.get("position", 0) or 0),
                    provider_metadata=dict(metadata) if isinstance(metadata, dict) else {},
                )
            )
    provider_raw = str(raw.get("provider_id", ProviderId.APPLE_MUSIC.value))
    try:
        provider_id = ProviderId(provider_raw)
    except ValueError:
        provider_id = ProviderId.APPLE_MUSIC
    checksum = str(raw.get("checksum", ""))
    if not checksum and tracks:
        checksum = remote_playlist_snapshot_checksum(tuple(tracks))
    return RemotePlaylistSnapshot(
        provider_id=provider_id,
        remote_playlist_id=str(raw.get("remote_playlist_id", "")),
        name=str(raw.get("name", "")),
        snapshot_at_iso=str(raw.get("snapshot_at_iso", "")),
        tracks=tuple(tracks),
        track_count=int(raw.get("track_count", len(tracks)) or len(tracks)),
        checksum=checksum,
        source_kind=str(raw.get("source_kind", "provider_library")),
        source_url=str(raw.get("source_url", "")),
    )
