from __future__ import annotations

from playlist_builder.app.playlist_sync.comparison import PlaylistComparisonService
from playlist_builder.app.playlist_sync.planner import PlaylistSyncPlanner
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail
from playlist_builder.ui.shared.dto.playlist_sync import PlaylistSyncPlan, SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot


class PlaylistSyncEngine:
    """Provider-neutral sync planning — produces plans only, never mutates providers."""

    def __init__(
        self,
        *,
        comparison_service: PlaylistComparisonService | None = None,
        planner: PlaylistSyncPlanner | None = None,
    ) -> None:
        self._comparison = comparison_service or PlaylistComparisonService()
        self._planner = planner or PlaylistSyncPlanner()

    def build_plan(
        self,
        *,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
        direction: SyncDirection,
        sync_mode: SyncMode = SyncMode.DRY_RUN,
    ) -> PlaylistSyncPlan:
        comparison = self._comparison.compare(local.tracks, remote.tracks)
        return self._planner.build_plan(
            local=local,
            remote=remote,
            direction=direction,
            sync_mode=sync_mode,
            comparison=comparison,
        )

    def dry_run(
        self,
        *,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
        direction: SyncDirection,
    ) -> PlaylistSyncPlan:
        """Deterministic dry-run — equivalent to build_plan with sync_mode=dry_run."""
        return self.build_plan(
            local=local,
            remote=remote,
            direction=direction,
            sync_mode=SyncMode.DRY_RUN,
        )
