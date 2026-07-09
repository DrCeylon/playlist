from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.canonical.identity import track_identity_key
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistTrack
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistTrack


@dataclass(frozen=True, slots=True)
class MatchedTrackPair:
    track_key: str
    local: ManagedPlaylistTrack
    remote: RemotePlaylistTrack


@dataclass(frozen=True, slots=True)
class MetadataMismatch:
    track_key: str
    local: ManagedPlaylistTrack
    remote: RemotePlaylistTrack
    fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlaylistComparisonResult:
    matched: tuple[MatchedTrackPair, ...]
    only_local: tuple[ManagedPlaylistTrack, ...]
    only_remote: tuple[RemotePlaylistTrack, ...]
    metadata_mismatches: tuple[MetadataMismatch, ...]
    local_duplicates: tuple[str, ...]
    remote_duplicates: tuple[str, ...]


class PlaylistComparisonService:
    """Provider-neutral diff between a local managed playlist and a remote snapshot."""

    def compare(
        self,
        local_tracks: tuple[ManagedPlaylistTrack, ...],
        remote_tracks: tuple[RemotePlaylistTrack, ...],
    ) -> PlaylistComparisonResult:
        local_by_key = self._index_local(local_tracks)
        remote_by_key = self._index_remote(remote_tracks)

        local_dupes = tuple(key for key, items in local_by_key.items() if len(items) > 1)
        remote_dupes = tuple(key for key, items in remote_by_key.items() if len(items) > 1)

        matched: list[MatchedTrackPair] = []
        metadata_mismatches: list[MetadataMismatch] = []
        only_local: list[ManagedPlaylistTrack] = []
        only_remote: list[RemotePlaylistTrack] = []

        for key, local_items in sorted(local_by_key.items()):
            remote_items = remote_by_key.get(key)
            if not remote_items:
                only_local.extend(local_items)
                continue
            local_track = local_items[0]
            remote_track = remote_items[0]
            mismatch_fields = self._metadata_diff_fields(local_track, remote_track)
            if mismatch_fields:
                metadata_mismatches.append(
                    MetadataMismatch(
                        track_key=key,
                        local=local_track,
                        remote=remote_track,
                        fields=mismatch_fields,
                    )
                )
            matched.append(MatchedTrackPair(track_key=key, local=local_track, remote=remote_track))

        for key, remote_items in sorted(remote_by_key.items()):
            if key not in local_by_key:
                only_remote.extend(remote_items)

        return PlaylistComparisonResult(
            matched=tuple(matched),
            only_local=tuple(only_local),
            only_remote=tuple(only_remote),
            metadata_mismatches=tuple(metadata_mismatches),
            local_duplicates=local_dupes,
            remote_duplicates=remote_dupes,
        )

    @staticmethod
    def _index_local(tracks: tuple[ManagedPlaylistTrack, ...]) -> dict[str, list[ManagedPlaylistTrack]]:
        indexed: dict[str, list[ManagedPlaylistTrack]] = {}
        for track in tracks:
            key = track_identity_key(track.artist, track.title)
            indexed.setdefault(key, []).append(track)
        return indexed

    @staticmethod
    def _index_remote(tracks: tuple[RemotePlaylistTrack, ...]) -> dict[str, list[RemotePlaylistTrack]]:
        indexed: dict[str, list[RemotePlaylistTrack]] = {}
        for track in tracks:
            key = track_identity_key(track.artist, track.title)
            indexed.setdefault(key, []).append(track)
        return indexed

    @staticmethod
    def _metadata_diff_fields(local: ManagedPlaylistTrack, remote: RemotePlaylistTrack) -> tuple[str, ...]:
        fields: list[str] = []
        local_provider_id = local.provider_track_id.strip()
        remote_provider_id = remote.remote_track_id.strip()
        if local_provider_id and remote_provider_id and local_provider_id != remote_provider_id:
            fields.append("provider_track_id")
        if remote.album.strip():
            fields.append("album")
        return tuple(fields)
