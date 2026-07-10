from __future__ import annotations

from pathlib import Path

from playlist_builder.app.bridge_runtime.backend import RuntimeEngineBridgeBackend
from playlist_builder.app.factory import build_app_context
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.bridge import BridgeCommand, JsonRpcEngineBridge
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack, remote_playlist_snapshot_checksum


def test_resolve_sync_conflicts_bridge_round_trip(tmp_path: Path) -> None:
    context = build_app_context()
    provider = RepositoryProvider(
        playlists_path=tmp_path / "managed_playlists.json",
        snapshots_dir=tmp_path / "snapshots",
        sync_operations_path=tmp_path / "sync_operations.json",
    )
    detail = ManagedPlaylistDetail(
        summary=ManagedPlaylistSummary(
            local_playlist_id="local-resolve",
            name="Resolve Demo",
            provider_id=ProviderId.APPLE_MUSIC,
            track_count=1,
            sync_status="pending",
            provider_playlist_id="remote-resolve",
        ),
        tracks=(ManagedPlaylistTrack(local_track_id="t1", artist="Kygo", title="Firestone"),),
    )
    provider.managed_playlist_repository().upsert(detail)

    tracks = (RemotePlaylistTrack(remote_track_id="r1", artist="Kygo", title="Firestone", album="Album", position=1),)
    remote = RemotePlaylistSnapshot(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id="remote-resolve",
        name="Resolve Demo",
        snapshot_at_iso="2026-07-10T12:00:00Z",
        tracks=tracks,
        track_count=1,
        checksum=remote_playlist_snapshot_checksum(tracks),
        source_kind="provider_library",
    )

    backend = RuntimeEngineBridgeBackend(context)
    backend._repository_provider = provider
    bridge = JsonRpcEngineBridge(backend=backend)

    plan_messages = bridge.handle(
        {
            "id": "plan-resolve",
            "command": BridgeCommand.PLAN_SYNC.value,
            "params": {
                "local_playlist_id": "local-resolve",
                "provider_id": "apple_music",
                "direction": "pull_from_provider",
                "sync_mode": "manual_resolve",
                "remote_playlist": remote.to_dict(),
            },
        }
    )
    assert plan_messages[-1]["ok"] is True
    conflicts = plan_messages[-1]["result"]["sync_plan"]["conflicts"]
    assert conflicts

    resolve_messages = bridge.handle(
        {
            "id": "resolve-1",
            "command": BridgeCommand.RESOLVE_SYNC_CONFLICTS.value,
            "params": {
                "local_playlist_id": "local-resolve",
                "provider_id": "apple_music",
                "direction": "pull_from_provider",
                "sync_mode": "manual_resolve",
                "remote_playlist": remote.to_dict(),
                "resolutions": [
                    {
                        "conflict_id": conflicts[0]["id"],
                        "strategy": conflicts[0].get("recommended_resolution") or "defer",
                    }
                ],
            },
        }
    )
    assert resolve_messages[-1]["ok"] is True, resolve_messages[-1]
    assert "plan_checksum" in resolve_messages[-1]["result"]
