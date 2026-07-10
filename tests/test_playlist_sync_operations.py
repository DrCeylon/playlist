from __future__ import annotations

from pathlib import Path

from playlist_builder.app.playlist_sync_operations.json_repository import JsonPlaylistSyncOperationRepository
from playlist_builder.app.playlist_sync_operations.serialization import operation_from_dict, operation_to_dict
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_sync import (
    PlaylistSyncOperation,
    SyncDirection,
    SyncMode,
    SyncOperationStatus,
)


def test_sync_operation_round_trip(tmp_path: Path) -> None:
    operation = PlaylistSyncOperation(
        operation_id="syncop-1",
        idempotency_key="idem-1",
        local_playlist_id="mpl-1",
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id="remote-1",
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.APPEND_ONLY,
        plan_checksum="abc",
        remote_snapshot_checksum="def",
        local_playlist_version_before=1,
        local_playlist_version_after=1,
        status=SyncOperationStatus.COMPLETED,
        created_at_iso="2026-07-10T10:00:00",
    )
    payload = operation_to_dict(operation)
    restored = operation_from_dict(payload)
    assert restored.operation_id == operation.operation_id
    assert restored.provider_id == ProviderId.APPLE_MUSIC
    repo = JsonPlaylistSyncOperationRepository(tmp_path / "sync_operations.json")
    repo.upsert(operation)
    loaded = repo.get_operation("syncop-1")
    assert loaded is not None
    assert loaded.status == SyncOperationStatus.COMPLETED
