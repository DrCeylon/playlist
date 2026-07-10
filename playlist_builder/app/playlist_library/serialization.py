from __future__ import annotations

from typing import Any

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_library import (
    LinkedRemoteRef,
    ManagedPlaylistDetail,
    ManagedPlaylistSummary,
    ManagedPlaylistTrack,
    PlaylistOrigin,
    PlaylistSyncConflict,
)

SCHEMA_VERSION = 1
ENTITY_VERSION_DEFAULT = 1


def linked_remote_ref_from_dict(raw: dict[str, Any]) -> LinkedRemoteRef:
    provider_raw = str(raw.get("provider_id", ProviderId.APPLE_MUSIC.value))
    try:
        provider_id = ProviderId(provider_raw)
    except ValueError:
        provider_id = ProviderId.APPLE_MUSIC
    return LinkedRemoteRef(
        provider_id=provider_id,
        remote_playlist_id=str(raw.get("remote_playlist_id", "")),
        snapshot_checksum=str(raw.get("snapshot_checksum", "")),
        sync_state=str(raw.get("sync_state", "")),
        last_sync_at=str(raw.get("last_sync_at", "")),
    )


def playlist_detail_from_dict(raw: dict[str, Any]) -> ManagedPlaylistDetail:
    provider_raw = str(raw.get("provider_id", ProviderId.APPLE_MUSIC.value))
    try:
        provider_id = ProviderId(provider_raw)
    except ValueError:
        provider_id = ProviderId.APPLE_MUSIC

    refs_raw = raw.get("linked_remote_refs", [])
    linked_refs: list[LinkedRemoteRef] = []
    if isinstance(refs_raw, list):
        for item in refs_raw:
            if isinstance(item, dict):
                linked_refs.append(linked_remote_ref_from_dict(item))

    summary = ManagedPlaylistSummary(
        local_playlist_id=str(raw.get("local_playlist_id", "")),
        name=str(raw.get("name", "")),
        provider_id=provider_id,
        track_count=int(raw.get("track_count", 0) or 0),
        sync_status=str(raw.get("sync_status", "unknown")),
        last_synced_at_iso=str(raw.get("last_synced_at_iso", "")),
        provider_playlist_id=str(raw.get("provider_playlist_id", "")),
        source_kind=str(raw.get("source_kind", "generated_import")),
        import_status=raw.get("import_status"),
        history_session_id=str(raw.get("history_session_id", "")),
        origin=str(raw.get("origin", PlaylistOrigin.GENERATED.value)),
        playlist_version=int(raw.get("playlist_version", ENTITY_VERSION_DEFAULT) or ENTITY_VERSION_DEFAULT),
        linked_remote_refs=tuple(linked_refs),
        created_at_iso=str(raw.get("created_at_iso", "")),
        updated_at_iso=str(raw.get("updated_at_iso", "")),
    )

    tracks_raw = raw.get("tracks", [])
    tracks: list[ManagedPlaylistTrack] = []
    if isinstance(tracks_raw, list):
        for item in tracks_raw:
            if not isinstance(item, dict):
                continue
            tracks.append(
                ManagedPlaylistTrack(
                    local_track_id=str(item.get("local_track_id", "")),
                    artist=str(item.get("artist", "")),
                    title=str(item.get("title", "")),
                    section=str(item.get("section", "")),
                    provider_track_id=str(item.get("provider_track_id", "")),
                    mapping_status=str(item.get("mapping_status", "matched")),
                )
            )

    conflicts_raw = raw.get("sync_conflicts", [])
    conflicts: list[PlaylistSyncConflict] = []
    if isinstance(conflicts_raw, list):
        for item in conflicts_raw:
            if not isinstance(item, dict):
                continue
            conflicts.append(
                PlaylistSyncConflict(
                    id=str(item.get("id", "")),
                    track_key=str(item.get("track_key", "")),
                    kind=str(item.get("kind", "")),
                    message=str(item.get("message", "")),
                )
            )

    return ManagedPlaylistDetail(summary=summary, tracks=tuple(tracks), sync_conflicts=tuple(conflicts))


def playlist_detail_to_dict(detail: ManagedPlaylistDetail) -> dict[str, Any]:
    return detail.to_dict()
