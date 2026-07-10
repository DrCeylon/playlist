from __future__ import annotations

import ast
from pathlib import Path


def test_playlist_sync_engine_has_no_integration_imports() -> None:
    root = Path("playlist_builder/app/playlist_sync")
    forbidden = "integration.apple_music"
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and forbidden in node.module:
                raise AssertionError(f"{path} imports {node.module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if forbidden in alias.name:
                        raise AssertionError(f"{path} imports {alias.name}")


def test_managed_playlist_repository_has_no_write_port_imports() -> None:
    root = Path("playlist_builder/app/playlist_library")
    forbidden = "playlist_write"
    for path in root.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert forbidden not in source, f"{path} must not reference write port"


def test_plan_sync_does_not_write_sync_operations(tmp_path: Path, monkeypatch) -> None:
    from playlist_builder.app.bridge_runtime.playlist_sync_plan import plan_sync
    from playlist_builder.canonical.enums import ProviderCapability, ProviderId
    from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
    from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary
    from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
    from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, remote_playlist_snapshot_checksum

    class _Gateway:
        provider_id = ProviderId.APPLE_MUSIC
        capabilities = frozenset({ProviderCapability.PLAYLIST_LIBRARY_BROWSE})

        @property
        def playlist_read(self):
            return None

    registry = ProviderGatewayRegistry()
    registry.register(_Gateway())  # type: ignore[arg-type]
    tracks = ()
    remote = RemotePlaylistSnapshot(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id="r1",
        name="Demo",
        snapshot_at_iso="2026-07-10T12:00:00",
        tracks=tracks,
        track_count=0,
        checksum=remote_playlist_snapshot_checksum(tracks),
        source_kind="provider_library",
    )
    local = ManagedPlaylistDetail(
        summary=ManagedPlaylistSummary(
            local_playlist_id="mpl-1",
            name="Demo",
            provider_id=ProviderId.APPLE_MUSIC,
            track_count=0,
            sync_status="pending",
        ),
        tracks=(),
    )
    ops_path = tmp_path / "sync_operations.json"
    plan_sync(
        registry,
        local_detail=local,
        remote_snapshot=remote,
        provider_id=ProviderId.APPLE_MUSIC,
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.DRY_RUN,
    )
    assert not ops_path.exists()
