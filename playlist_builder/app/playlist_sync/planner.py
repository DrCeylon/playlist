from __future__ import annotations

from typing import Any

from playlist_builder.app.playlist_sync.comparison import PlaylistComparisonResult
from playlist_builder.canonical.identity import track_identity_key
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistTrack, PlaylistSyncConflict
from playlist_builder.ui.shared.dto.playlist_sync import (
    PlaylistSyncAction,
    PlaylistSyncActionKind,
    PlaylistSyncPlan,
    PlaylistSyncSummary,
    SyncDirection,
    SyncMode,
)
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack


class PlaylistSyncPlanner:
    """Builds a deterministic sync plan from a comparison result — no provider I/O."""

    def build_plan(
        self,
        *,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
        direction: SyncDirection,
        sync_mode: SyncMode,
        comparison: PlaylistComparisonResult,
    ) -> PlaylistSyncPlan:
        actions: list[PlaylistSyncAction] = []
        stats: dict[str, Any] = {
            "additions": 0,
            "removals": 0,
            "already_present": len(comparison.matched),
            "metadata_mismatches": 0,
            "reorders": 0,
            "conflicts": 0,
            "rename_required": local.summary.name.strip() != remote.name.strip(),
        }

        if stats["rename_required"]:
            actions.append(
                PlaylistSyncAction(
                    kind=PlaylistSyncActionKind.RENAME_PLAYLIST,
                    track_key="",
                    artist="",
                    title="",
                    message=f"Renommer « {local.summary.name} » → « {remote.name} »",
                )
            )

        self._append_duplicate_conflicts(comparison, stats)

        allow_removals = sync_mode in {SyncMode.MIRROR, SyncMode.DRY_RUN}

        if direction == SyncDirection.PULL_FROM_PROVIDER:
            self._plan_additions(comparison.only_remote, actions, stats, target="local")
            if allow_removals:
                self._plan_removals(comparison.only_local, actions, stats, source="local")
            self._plan_reorders_pull(local.tracks, remote.tracks, comparison, actions, stats)
        elif direction == SyncDirection.PUSH_TO_PROVIDER:
            self._plan_additions(comparison.only_local, actions, stats, target="provider")
            if allow_removals:
                self._plan_removals(comparison.only_remote, actions, stats, source="remote")
            self._plan_reorders_push(local.tracks, remote.tracks, comparison, actions, stats)
        else:
            self._plan_additions(comparison.only_remote, actions, stats, target="local")
            self._plan_removals(comparison.only_local, actions, stats, source="local")
            self._plan_additions(comparison.only_local, actions, stats, target="provider")
            self._plan_removals(comparison.only_remote, actions, stats, source="remote")

        self._plan_metadata(comparison, sync_mode, actions, stats)

        actions.sort(key=self._action_sort_key)

        from playlist_builder.app.playlist_sync.conflict_detector import PlaylistConflictDetector, SyncConflictContext

        detector = PlaylistConflictDetector()
        conflicts = detector.detect(
            local=local,
            remote=remote,
            comparison=comparison,
            actions=tuple(actions),
            context=SyncConflictContext(
                provider_id=remote.provider_id,
                direction=direction,
                sync_mode=sync_mode,
            ),
        )
        stats["conflicts"] = len(conflicts)

        summary = PlaylistSyncSummary(
            additions=stats["additions"],
            removals=stats["removals"],
            already_present=stats["already_present"],
            metadata_mismatches=stats["metadata_mismatches"],
            reorders=stats["reorders"],
            conflicts=stats["conflicts"],
            rename_required=stats["rename_required"],
        )

        return PlaylistSyncPlan(
            local_playlist_id=local.summary.local_playlist_id,
            target_provider_id=remote.provider_id,
            direction=direction,
            sync_mode=sync_mode,
            remote_playlist_id=remote.remote_playlist_id,
            actions=tuple(actions),
            conflicts=conflicts,
            summary=summary,
            playlist_name_local=local.summary.name,
            playlist_name_remote=remote.name,
        )

    def _plan_additions(
        self,
        tracks: tuple[ManagedPlaylistTrack, ...] | tuple[RemotePlaylistTrack, ...],
        actions: list[PlaylistSyncAction],
        stats: dict[str, Any],
        *,
        target: str,
    ) -> None:
        for track in tracks:
            if isinstance(track, ManagedPlaylistTrack):
                actions.append(
                    PlaylistSyncAction(
                        kind=PlaylistSyncActionKind.ADD_TRACK,
                        track_key=track_identity_key(track.artist, track.title),
                        artist=track.artist,
                        title=track.title,
                        local_track_id=track.local_track_id,
                        message=f"Ajouter vers {target}",
                    )
                )
            else:
                actions.append(
                    PlaylistSyncAction(
                        kind=PlaylistSyncActionKind.ADD_TRACK,
                        track_key=track_identity_key(track.artist, track.title),
                        artist=track.artist,
                        title=track.title,
                        remote_track_id=track.remote_track_id,
                        source_position=track.position,
                        message=f"Ajouter vers {target}",
                    )
                )
            stats["additions"] += 1

    def _plan_removals(
        self,
        tracks: tuple[ManagedPlaylistTrack, ...] | tuple[RemotePlaylistTrack, ...],
        actions: list[PlaylistSyncAction],
        stats: dict[str, Any],
        *,
        source: str,
    ) -> None:
        for track in tracks:
            if isinstance(track, ManagedPlaylistTrack):
                actions.append(
                    PlaylistSyncAction(
                        kind=PlaylistSyncActionKind.REMOVE_TRACK,
                        track_key=track_identity_key(track.artist, track.title),
                        artist=track.artist,
                        title=track.title,
                        local_track_id=track.local_track_id,
                        message=f"Retirer depuis {source}",
                    )
                )
            else:
                actions.append(
                    PlaylistSyncAction(
                        kind=PlaylistSyncActionKind.REMOVE_TRACK,
                        track_key=track_identity_key(track.artist, track.title),
                        artist=track.artist,
                        title=track.title,
                        remote_track_id=track.remote_track_id,
                        source_position=track.position,
                        message=f"Retirer depuis {source}",
                    )
                )
            stats["removals"] += 1

    def _plan_reorders_pull(
        self,
        local_tracks: tuple[ManagedPlaylistTrack, ...],
        remote_tracks: tuple[RemotePlaylistTrack, ...],
        comparison: PlaylistComparisonResult,
        actions: list[PlaylistSyncAction],
        stats: dict[str, Any],
    ) -> None:
        local_pos = _position_index(local_tracks)
        remote_pos = _position_index_remote(remote_tracks)
        for pair in comparison.matched:
            current = local_pos.get(pair.track_key)
            desired = remote_pos.get(pair.track_key)
            if current is None or desired is None or current == desired:
                continue
            actions.append(
                PlaylistSyncAction(
                    kind=PlaylistSyncActionKind.REORDER,
                    track_key=pair.track_key,
                    artist=pair.local.artist,
                    title=pair.local.title,
                    source_position=current,
                    target_position=desired,
                    message=f"Réordonner localement ({current} → {desired})",
                )
            )
            stats["reorders"] += 1

    def _plan_reorders_push(
        self,
        local_tracks: tuple[ManagedPlaylistTrack, ...],
        remote_tracks: tuple[RemotePlaylistTrack, ...],
        comparison: PlaylistComparisonResult,
        actions: list[PlaylistSyncAction],
        stats: dict[str, Any],
    ) -> None:
        local_pos = _position_index(local_tracks)
        remote_pos = _position_index_remote(remote_tracks)
        for pair in comparison.matched:
            current = remote_pos.get(pair.track_key)
            desired = local_pos.get(pair.track_key)
            if current is None or desired is None or current == desired:
                continue
            actions.append(
                PlaylistSyncAction(
                    kind=PlaylistSyncActionKind.REORDER,
                    track_key=pair.track_key,
                    artist=pair.local.artist,
                    title=pair.local.title,
                    source_position=current,
                    target_position=desired,
                    message=f"Réordonner côté provider ({current} → {desired})",
                )
            )
            stats["reorders"] += 1

    def _plan_metadata(
        self,
        comparison: PlaylistComparisonResult,
        sync_mode: SyncMode,
        actions: list[PlaylistSyncAction],
        stats: dict[str, Any],
    ) -> None:
        for mismatch in comparison.metadata_mismatches:
            if sync_mode == SyncMode.MANUAL_RESOLVE:
                stats["metadata_mismatches"] += 1
                continue
            actions.append(
                PlaylistSyncAction(
                    kind=PlaylistSyncActionKind.MAP_TRACK,
                    track_key=mismatch.track_key,
                    artist=mismatch.local.artist,
                    title=mismatch.local.title,
                    local_track_id=mismatch.local.local_track_id,
                    remote_track_id=mismatch.remote.remote_track_id,
                    message=f"Mapper métadonnées ({', '.join(mismatch.fields)})",
                )
            )
            stats["metadata_mismatches"] += 1

    @staticmethod
    def _append_duplicate_conflicts(
        comparison: PlaylistComparisonResult,
        stats: dict[str, Any],
    ) -> None:
        del comparison, stats

    @staticmethod
    def _action_sort_key(action: PlaylistSyncAction) -> tuple[str, str, int]:
        kind_order = {
            PlaylistSyncActionKind.RENAME_PLAYLIST.value: "0",
            PlaylistSyncActionKind.REMOVE_TRACK.value: "1",
            PlaylistSyncActionKind.ADD_TRACK.value: "2",
            PlaylistSyncActionKind.MAP_TRACK.value: "3",
            PlaylistSyncActionKind.REORDER.value: "4",
        }
        return (
            kind_order.get(action.kind.value, "9"),
            action.track_key,
            action.target_position or action.source_position or 0,
        )


def _position_index(tracks: tuple[ManagedPlaylistTrack, ...]) -> dict[str, int]:
    positions: dict[str, int] = {}
    for index, track in enumerate(tracks, start=1):
        key = track_identity_key(track.artist, track.title)
        positions.setdefault(key, index)
    return positions


def _position_index_remote(tracks: tuple[RemotePlaylistTrack, ...]) -> dict[str, int]:
    positions: dict[str, int] = {}
    for track in tracks:
        key = track_identity_key(track.artist, track.title)
        position = track.position if track.position > 0 else len(positions) + 1
        positions.setdefault(key, position)
    if not positions and tracks:
        for index, track in enumerate(tracks, start=1):
            key = track_identity_key(track.artist, track.title)
            positions.setdefault(key, index)
    return positions
