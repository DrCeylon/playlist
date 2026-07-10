from __future__ import annotations

from typing import Protocol, runtime_checkable

from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail


@runtime_checkable
class ManagedPlaylistRepository(Protocol):
    """CRUD for managed playlists — no sync or provider knowledge."""

    def list_playlists(self) -> list[ManagedPlaylistDetail]: ...

    def get_playlist(self, local_playlist_id: str) -> ManagedPlaylistDetail | None: ...

    def upsert(self, detail: ManagedPlaylistDetail) -> ManagedPlaylistDetail: ...

    def delete(self, local_playlist_id: str) -> bool: ...
