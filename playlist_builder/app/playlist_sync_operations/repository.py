from __future__ import annotations

from typing import Protocol, runtime_checkable

from playlist_builder.ui.shared.dto.playlist_sync import PlaylistSyncOperation


@runtime_checkable
class PlaylistSyncOperationRepository(Protocol):
    def list_operations(self) -> list[PlaylistSyncOperation]: ...

    def get_operation(self, operation_id: str) -> PlaylistSyncOperation | None: ...

    def get_by_idempotency_key(self, idempotency_key: str) -> PlaylistSyncOperation | None: ...

    def upsert(self, operation: PlaylistSyncOperation) -> PlaylistSyncOperation: ...
