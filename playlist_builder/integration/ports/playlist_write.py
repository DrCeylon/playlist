from __future__ import annotations

from typing import Protocol, runtime_checkable

from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistTrack


@runtime_checkable
class ProviderPlaylistWritePort(Protocol):
    """Create or mutate playlists on a connected provider account."""

    def create_playlist(self, name: str) -> str: ...

    def upsert_tracks(self, remote_playlist_id: str, tracks: tuple[RemotePlaylistTrack, ...]) -> None: ...

    def remove_tracks(self, remote_playlist_id: str, remote_track_ids: tuple[str, ...]) -> None: ...
