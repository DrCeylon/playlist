from __future__ import annotations

from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistTrack
from playlist_builder.ui.shared.dto.playlist_sync import PlaylistSyncAction, PlaylistSyncActionKind, SyncActionOutcome
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistTrack


class SyncActionExecutor:
    """Executes individual sync actions via write port or local mutations."""

    def execute_push(
        self,
        action: PlaylistSyncAction,
        *,
        write_port: ProviderPlaylistWritePort,
        remote_playlist_id: str,
        action_id: str,
    ) -> SyncActionOutcome:
        if action.kind == PlaylistSyncActionKind.ADD_TRACK:
            track = RemotePlaylistTrack(
                remote_track_id=action.remote_track_id,
                artist=action.artist,
                title=action.title,
                position=action.target_position or action.source_position or 0,
            )
            try:
                write_port.upsert_tracks(remote_playlist_id, (track,))
            except Exception as exc:
                return SyncActionOutcome(
                    action_id=action_id,
                    kind=action.kind.value,
                    track_key=action.track_key,
                    status="failed",
                    message=str(exc),
                )
            return SyncActionOutcome(
                action_id=action_id,
                kind=action.kind.value,
                track_key=action.track_key,
                status="completed",
                message="Morceau ajouté côté provider.",
            )

        if action.kind == PlaylistSyncActionKind.REMOVE_TRACK:
            if not action.remote_track_id:
                return SyncActionOutcome(
                    action_id=action_id,
                    kind=action.kind.value,
                    track_key=action.track_key,
                    status="failed",
                    message="remote_track_id manquant pour la suppression.",
                )
            try:
                write_port.remove_tracks(remote_playlist_id, (action.remote_track_id,))
            except Exception as exc:
                return SyncActionOutcome(
                    action_id=action_id,
                    kind=action.kind.value,
                    track_key=action.track_key,
                    status="failed",
                    message=str(exc),
                )
            return SyncActionOutcome(
                action_id=action_id,
                kind=action.kind.value,
                track_key=action.track_key,
                status="completed",
                message="Morceau retiré côté provider.",
            )

        return SyncActionOutcome(
            action_id=action_id,
            kind=action.kind.value,
            track_key=action.track_key,
            status="skipped",
            message=f"Action {action.kind.value} non supportée en 6.5.",
        )

    def pull_track_from_action(
        self,
        action: PlaylistSyncAction,
        *,
        local_playlist_id: str,
        index: int,
    ) -> ManagedPlaylistTrack:
        return ManagedPlaylistTrack(
            local_track_id=f"{local_playlist_id}-pull-{index}",
            artist=action.artist,
            title=action.title,
            provider_track_id=action.remote_track_id,
            mapping_status="matched",
        )
