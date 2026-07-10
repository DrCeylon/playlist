from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from playlist_builder.app.playlist_library.repository import ManagedPlaylistRepository
from playlist_builder.app.playlist_library.snapshot_archive import SnapshotArchive
from playlist_builder.ui.shared.dto.playlist_library import (
    LinkedRemoteRef,
    ManagedPlaylistDetail,
    ManagedPlaylistSummary,
    ManagedPlaylistTrack,
    PlaylistOrigin,
)
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, remote_playlist_snapshot_checksum


class ImportRemotePlaylist:
    """Pure use case: RemotePlaylistSnapshot → ManagedPlaylistDetail → persist.

    No provider gateway, no Apple/Spotify/YouTube knowledge.
    """

    def __init__(
        self,
        repository: ManagedPlaylistRepository,
        snapshots: SnapshotArchive,
    ) -> None:
        self._repository = repository
        self._snapshots = snapshots

    def execute(
        self,
        snapshot: RemotePlaylistSnapshot,
        *,
        origin: str = PlaylistOrigin.PROVIDER_LIBRARY.value,
        local_playlist_id: str | None = None,
    ) -> ManagedPlaylistDetail:
        checksum = snapshot.checksum or remote_playlist_snapshot_checksum(snapshot.tracks)
        self._snapshots.store(snapshot)

        linked_ref = LinkedRemoteRef(
            provider_id=snapshot.provider_id,
            remote_playlist_id=snapshot.remote_playlist_id,
            snapshot_checksum=checksum,
        )

        tracks = tuple(
            ManagedPlaylistTrack(
                local_track_id=f"mtr-{checksum}-{index}",
                artist=track.artist,
                title=track.title,
                provider_track_id=track.remote_track_id,
                mapping_status="matched",
            )
            for index, track in enumerate(snapshot.tracks)
        )

        now = datetime.now().isoformat(timespec="seconds")
        playlist_id = (local_playlist_id or "").strip() or f"mpl-{uuid4()}"

        summary = ManagedPlaylistSummary(
            local_playlist_id=playlist_id,
            name=snapshot.name,
            provider_id=snapshot.provider_id,
            track_count=len(tracks),
            sync_status="synced",
            last_synced_at_iso=snapshot.snapshot_at_iso or now,
            provider_playlist_id=snapshot.remote_playlist_id,
            source_kind="provider_library",
            origin=origin,
            playlist_version=1,
            linked_remote_refs=(linked_ref,),
            created_at_iso=now,
            updated_at_iso=now,
        )
        detail = ManagedPlaylistDetail(summary=summary, tracks=tracks)
        self._repository.upsert(detail)
        return detail
