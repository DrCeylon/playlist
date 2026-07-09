from __future__ import annotations

from typing import Protocol, runtime_checkable

from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylist, RemotePlaylistSnapshot


@runtime_checkable
class ProviderPlaylistReadPort(Protocol):
    """Read playlists and tracks from a connected provider account."""

    def list_playlists(self, *, account_id: str | None = None) -> tuple[RemotePlaylist, ...]: ...

    def get_playlist(self, remote_playlist_id: str) -> RemotePlaylistSnapshot: ...
