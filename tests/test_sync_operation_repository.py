from __future__ import annotations

from pathlib import Path

import pytest

from playlist_builder.app.playlist_library.errors import UnsupportedSchemaVersionError
from playlist_builder.app.playlist_sync_operations.json_repository import JsonPlaylistSyncOperationRepository
from playlist_builder.app.playlist_sync_operations.serialization import SCHEMA_VERSION


def test_sync_operation_repository_rejects_forward_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "sync_operations.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'{{"schema_version": {SCHEMA_VERSION + 1}, "operations": []}}',
        encoding="utf-8",
    )
    repository = JsonPlaylistSyncOperationRepository(path)
    with pytest.raises(UnsupportedSchemaVersionError):
        repository.list_operations()
