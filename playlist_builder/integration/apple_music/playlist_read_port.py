from __future__ import annotations

from datetime import UTC, datetime

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.ui.shared.dto.remote_playlist import (
    RemotePlaylist,
    RemotePlaylistSnapshot,
    RemotePlaylistTrack,
    remote_playlist_snapshot_checksum,
)


class AppleMusicPlaylistReadPort(ProviderPlaylistReadPort):
    """Read user playlists from Music.app via AppleScript."""

    def __init__(self, applescript: AppleScriptClient) -> None:
        self._applescript = applescript

    def list_playlists(self, *, account_id: str | None = None) -> tuple[RemotePlaylist, ...]:
        del account_id
        snapshot_at = _utc_now_iso()
        playlists: list[RemotePlaylist] = []
        for playlist_id, name, track_count in self._applescript.list_user_playlists():
            playlists.append(
                RemotePlaylist(
                    provider_id=ProviderId.APPLE_MUSIC,
                    remote_playlist_id=playlist_id,
                    name=name,
                    track_count=track_count,
                    is_public=False,
                    owner_label="Apple Music",
                    snapshot_at_iso=snapshot_at,
                )
            )
        return tuple(playlists)

    def get_playlist(self, remote_playlist_id: str) -> RemotePlaylistSnapshot:
        playlist_id = remote_playlist_id.strip()
        if not playlist_id:
            raise ValueError("remote_playlist_id is required.")

        playlist_name = ""
        for listed_id, name, _ in self._applescript.list_user_playlists():
            if listed_id == playlist_id:
                playlist_name = name
                break

        tracks: list[RemotePlaylistTrack] = []
        for remote_track_id, artist, title, album, duration_ms, position in self._applescript.load_playlist_tracks_by_id(
            playlist_id
        ):
            tracks.append(
                RemotePlaylistTrack(
                    remote_track_id=remote_track_id,
                    artist=artist,
                    title=title,
                    album=album,
                    duration_ms=duration_ms,
                    position=position,
                )
            )

        track_tuple = tuple(tracks)
        snapshot_at = _utc_now_iso()
        return RemotePlaylistSnapshot(
            provider_id=ProviderId.APPLE_MUSIC,
            remote_playlist_id=playlist_id,
            name=playlist_name or playlist_id,
            snapshot_at_iso=snapshot_at,
            tracks=track_tuple,
            track_count=len(track_tuple),
            checksum=remote_playlist_snapshot_checksum(track_tuple),
            source_kind="provider_library",
        )


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
