from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from playlist_builder.app.playlist_library.json_repository import JsonManagedPlaylistRepository
from playlist_builder.app.playlist_library.repository import ManagedPlaylistRepository
from playlist_builder.app.playlist_library.snapshot_archive import SnapshotArchive
from playlist_builder.app.playlist_sync_operations.json_repository import JsonPlaylistSyncOperationRepository
from playlist_builder.app.playlist_sync_operations.repository import PlaylistSyncOperationRepository


@dataclass
class RepositoryProvider:
    """Returns repository backends — use cases depend on this, not concrete JSON."""

    playlists_path: Path = Path("data/playlists/managed_playlists.json")
    snapshots_dir: Path = Path("data/playlists/snapshots")
    sync_operations_path: Path = Path("data/playlists/sync_operations.json")
    _repository: ManagedPlaylistRepository | None = field(default=None, init=False, repr=False)
    _archive: SnapshotArchive | None = field(default=None, init=False, repr=False)
    _sync_operations: PlaylistSyncOperationRepository | None = field(default=None, init=False, repr=False)

    def managed_playlist_repository(self) -> ManagedPlaylistRepository:
        if self._repository is None:
            self._repository = JsonManagedPlaylistRepository(self.playlists_path)
        return self._repository

    def snapshot_archive(self) -> SnapshotArchive:
        if self._archive is None:
            self._archive = SnapshotArchive(self.snapshots_dir)
        return self._archive

    def sync_operation_repository(self) -> PlaylistSyncOperationRepository:
        if self._sync_operations is None:
            self._sync_operations = JsonPlaylistSyncOperationRepository(self.sync_operations_path)
        return self._sync_operations
