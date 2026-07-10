from __future__ import annotations

import json
from pathlib import Path

from playlist_builder.app.playlist_library.errors import (
    SnapshotChecksumMismatchError,
    SnapshotCorruptionError,
)
from playlist_builder.infrastructure.atomic_json import advisory_file_lock, replace_file_atomic
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
        lock_path = path.with_suffix(f"{path.suffix}.lock")
        with advisory_file_lock(lock_path):
            if path.exists():
                _assert_snapshot_checksum_on_disk(path, checksum)
                return checksum
            payload = snapshot.to_dict()
            payload["checksum"] = checksum
            payload["snapshot_id"] = snapshot_id_from_checksum(checksum)
            replace_file_atomic(
                path,
                json.dumps(payload, indent=2, ensure_ascii=False),
            )
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


def _assert_snapshot_checksum_on_disk(path: Path, expected_checksum: str) -> None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotCorruptionError(str(path), str(exc)) from exc
    if not isinstance(raw, dict):
        raise SnapshotCorruptionError(str(path), "root is not a JSON object")
    stored = str(raw.get("checksum", ""))
    if stored != expected_checksum:
        raise SnapshotChecksumMismatchError(str(path), expected_checksum, stored)


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
    from playlist_builder.canonical.provider_ids import parse_provider_id

    provider_id = parse_provider_id(raw.get("provider_id"), default=ProviderId.APPLE_MUSIC)
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
