from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.validation import dto_to_dict


class PlaylistOrigin(StrEnum):
    PROVIDER_LIBRARY = "provider_library"
    GENERATED = "generated"
    IMPORTED_FILE = "imported_file"
    MANUAL = "manual"
    SHARED = "shared"


@dataclass(frozen=True, slots=True)
class LinkedRemoteRef:
    provider_id: ProviderId
    remote_playlist_id: str
    snapshot_checksum: str = ""
    last_seen_snapshot_checksum: str = ""
    last_applied_snapshot_checksum: str = ""
    sync_state: str = ""
    last_sync_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = dto_to_dict(self)
        payload["provider_id"] = self.provider_id.value
        seen = self.last_seen_snapshot_checksum or self.snapshot_checksum
        if seen:
            payload["last_seen_snapshot_checksum"] = seen
        if self.snapshot_checksum:
            payload["snapshot_checksum"] = self.snapshot_checksum
        return payload


def linked_remote_ref_from_dict(raw: dict[str, Any]) -> LinkedRemoteRef:
    provider_raw = str(raw.get("provider_id", ProviderId.APPLE_MUSIC.value))
    try:
        provider_id = ProviderId(provider_raw)
    except ValueError:
        provider_id = ProviderId.APPLE_MUSIC
    legacy_checksum = str(raw.get("snapshot_checksum", ""))
    last_seen = str(raw.get("last_seen_snapshot_checksum", "")) or legacy_checksum
    last_applied = str(raw.get("last_applied_snapshot_checksum", ""))
    return LinkedRemoteRef(
        provider_id=provider_id,
        remote_playlist_id=str(raw.get("remote_playlist_id", "")),
        snapshot_checksum=legacy_checksum or last_seen,
        last_seen_snapshot_checksum=last_seen,
        last_applied_snapshot_checksum=last_applied,
        sync_state=str(raw.get("sync_state", "")),
        last_sync_at=str(raw.get("last_sync_at", "")),
    )


@dataclass(frozen=True, slots=True)
class ManagedPlaylistSummary:
    local_playlist_id: str
    name: str
    provider_id: ProviderId
    track_count: int
    sync_status: str
    last_synced_at_iso: str = ""
    provider_playlist_id: str = ""
    source_kind: str = "generated_import"
    import_status: str | None = None
    history_session_id: str = ""
    origin: str = PlaylistOrigin.GENERATED.value
    playlist_version: int = 1
    linked_remote_refs: tuple[LinkedRemoteRef, ...] = ()
    created_at_iso: str = ""
    updated_at_iso: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = dto_to_dict(self)
        payload["provider_id"] = self.provider_id.value
        payload["linked_remote_refs"] = [ref.to_dict() for ref in self.linked_remote_refs]
        return payload


@dataclass(frozen=True, slots=True)
class ManagedPlaylistTrack:
    local_track_id: str
    artist: str
    title: str
    section: str = ""
    provider_track_id: str = ""
    mapping_status: str = "matched"

    def to_dict(self) -> dict[str, Any]:
        return dto_to_dict(self)


@dataclass(frozen=True, slots=True)
class PlaylistSyncConflict:
    id: str
    track_key: str
    kind: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return dto_to_dict(self)


@dataclass(frozen=True, slots=True)
class ManagedPlaylistDetail:
    summary: ManagedPlaylistSummary
    tracks: tuple[ManagedPlaylistTrack, ...] = ()
    sync_conflicts: tuple[PlaylistSyncConflict, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.summary.to_dict(),
            "tracks": [track.to_dict() for track in self.tracks],
            "sync_conflicts": [conflict.to_dict() for conflict in self.sync_conflicts],
        }


@dataclass(frozen=True, slots=True)
class PlaylistSyncResult:
    local_playlist_id: str
    sync_status: str
    message: str
    conflicts: tuple[PlaylistSyncConflict, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_playlist_id": self.local_playlist_id,
            "sync_status": self.sync_status,
            "message": self.message,
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
        }


def managed_playlist_from_history_session(session: dict[str, Any]) -> ManagedPlaylistSummary | None:
    """Build a summary from a history session — used only for lazy migration."""
    session_id = str(session.get("session_id", "")).strip()
    playlist_name = str(session.get("playlist_name", "")).strip()
    if not session_id or not playlist_name:
        return None
    provider_raw = str(session.get("provider_id", ProviderId.APPLE_MUSIC.value))
    try:
        provider_id = ProviderId(provider_raw)
    except ValueError:
        provider_id = ProviderId.APPLE_MUSIC
    status = str(session.get("status", ""))
    sync_status = "synced" if status == "imported" else "partial" if status == "partial_success" else "pending"
    finished_at = str(session.get("finished_at_iso", "") or "")
    return ManagedPlaylistSummary(
        local_playlist_id=f"hist-{session_id}",
        name=playlist_name,
        provider_id=provider_id,
        track_count=int(session.get("track_count", 0) or 0),
        sync_status=sync_status,
        last_synced_at_iso=finished_at,
        provider_playlist_id="",
        source_kind="generated_import",
        import_status=status or None,
        history_session_id=session_id,
        origin=PlaylistOrigin.GENERATED.value,
        playlist_version=1,
        created_at_iso=str(session.get("started_at_iso", "") or ""),
        updated_at_iso=finished_at,
    )
