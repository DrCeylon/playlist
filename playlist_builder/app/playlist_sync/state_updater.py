from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from playlist_builder.canonical.identity import track_identity_key
from playlist_builder.ui.shared.dto.playlist_library import (
    LinkedRemoteRef,
    ManagedPlaylistDetail,
    ManagedPlaylistSummary,
    ManagedPlaylistTrack,
)
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_sync import SyncOperationStatus


class PlaylistSyncStateUpdater:
    """Updates managed playlist sync metadata after an apply — not generic CRUD."""

    def apply_success(
        self,
        detail: ManagedPlaylistDetail,
        *,
        provider_id: ProviderId,
        remote_playlist_id: str,
        remote_snapshot_checksum: str,
        sync_status: str,
        local_content_changed: bool,
    ) -> ManagedPlaylistDetail:
        now = datetime.now().isoformat(timespec="seconds")
        refs = _update_linked_ref(
            detail.summary.linked_remote_refs,
            provider_id=provider_id,
            remote_playlist_id=remote_playlist_id,
            remote_snapshot_checksum=remote_snapshot_checksum,
            sync_state=sync_status,
            last_sync_at=now,
            advance_applied=True,
        )
        new_version = detail.summary.playlist_version + (1 if local_content_changed else 0)
        summary = replace(
            detail.summary,
            sync_status=sync_status,
            last_synced_at_iso=now,
            playlist_version=new_version,
            linked_remote_refs=refs,
            updated_at_iso=now,
            provider_playlist_id=remote_playlist_id or detail.summary.provider_playlist_id,
        )
        return ManagedPlaylistDetail(summary=summary, tracks=detail.tracks, sync_conflicts=detail.sync_conflicts)

    def apply_partial(
        self,
        detail: ManagedPlaylistDetail,
        *,
        provider_id: ProviderId,
        remote_playlist_id: str,
        remote_snapshot_checksum: str,
    ) -> ManagedPlaylistDetail:
        now = datetime.now().isoformat(timespec="seconds")
        refs = _update_linked_ref(
            detail.summary.linked_remote_refs,
            provider_id=provider_id,
            remote_playlist_id=remote_playlist_id,
            remote_snapshot_checksum=remote_snapshot_checksum,
            sync_state="partial",
            last_sync_at=now,
            advance_applied=False,
        )
        summary = replace(
            detail.summary,
            sync_status="partial",
            linked_remote_refs=refs,
            updated_at_iso=now,
        )
        return ManagedPlaylistDetail(summary=summary, tracks=detail.tracks, sync_conflicts=detail.sync_conflicts)

    def apply_no_op(self, detail: ManagedPlaylistDetail, *, provider_id: ProviderId, remote_playlist_id: str) -> ManagedPlaylistDetail:
        refs = _update_linked_ref(
            detail.summary.linked_remote_refs,
            provider_id=provider_id,
            remote_playlist_id=remote_playlist_id,
            remote_snapshot_checksum="",
            sync_state="synced",
            last_sync_at=detail.summary.last_synced_at_iso,
            advance_applied=False,
            seen_only=True,
        )
        summary = replace(detail.summary, linked_remote_refs=refs)
        return ManagedPlaylistDetail(summary=summary, tracks=detail.tracks, sync_conflicts=detail.sync_conflicts)

    def apply_pull_tracks(
        self,
        detail: ManagedPlaylistDetail,
        new_tracks: tuple[ManagedPlaylistTrack, ...],
    ) -> ManagedPlaylistDetail:
        merged = list(detail.tracks)
        existing = {track_identity_key(track.artist, track.title) for track in merged}
        changed = False
        for track in new_tracks:
            key = track_identity_key(track.artist, track.title)
            if key in existing:
                continue
            merged.append(track)
            existing.add(key)
            changed = True
        if not changed:
            return detail
        summary = replace(
            detail.summary,
            track_count=len(merged),
            playlist_version=detail.summary.playlist_version + 1,
            updated_at_iso=datetime.now().isoformat(timespec="seconds"),
        )
        return ManagedPlaylistDetail(summary=summary, tracks=tuple(merged), sync_conflicts=detail.sync_conflicts)


def _update_linked_ref(
    refs: tuple[LinkedRemoteRef, ...],
    *,
    provider_id: ProviderId,
    remote_playlist_id: str,
    remote_snapshot_checksum: str,
    sync_state: str,
    last_sync_at: str,
    advance_applied: bool,
    seen_only: bool = False,
) -> tuple[LinkedRemoteRef, ...]:
    updated: list[LinkedRemoteRef] = []
    replaced = False
    for ref in refs:
        if ref.provider_id == provider_id and ref.remote_playlist_id == remote_playlist_id:
            seen = remote_snapshot_checksum or ref.last_seen_snapshot_checksum or ref.snapshot_checksum
            applied = ref.last_applied_snapshot_checksum
            if advance_applied and remote_snapshot_checksum:
                applied = remote_snapshot_checksum
            updated.append(
                LinkedRemoteRef(
                    provider_id=ref.provider_id,
                    remote_playlist_id=ref.remote_playlist_id,
                    snapshot_checksum=seen,
                    last_seen_snapshot_checksum=seen if not seen_only else ref.last_seen_snapshot_checksum,
                    last_applied_snapshot_checksum=applied,
                    sync_state=sync_state,
                    last_sync_at=last_sync_at,
                )
            )
            replaced = True
        else:
            updated.append(ref)
    if not replaced and remote_playlist_id:
        seen = remote_snapshot_checksum
        updated.append(
            LinkedRemoteRef(
                provider_id=provider_id,
                remote_playlist_id=remote_playlist_id,
                snapshot_checksum=seen,
                last_seen_snapshot_checksum=seen,
                last_applied_snapshot_checksum=seen if advance_applied else "",
                sync_state=sync_state,
                last_sync_at=last_sync_at,
            )
        )
    return tuple(updated)
