from __future__ import annotations

from pathlib import Path

from playlist_builder.app.bridge_runtime.playlist_sync_apply import apply_sync
from playlist_builder.app.bridge_runtime.playlist_sync_plan import plan_sync
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.ui.bridge import BridgeCommand, JsonRpcEngineBridge
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack, remote_playlist_snapshot_checksum


class _FakeWritePort(ProviderPlaylistWritePort):
    def create_playlist(self, name: str) -> str:
        return "remote-target"

    def upsert_tracks(self, remote_playlist_id: str, tracks: tuple[RemotePlaylistTrack, ...]) -> None:
        return None

    def remove_tracks(self, remote_playlist_id: str, remote_track_ids: tuple[str, ...]) -> None:
        return None


class _PlanningGateway:
    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.APPLE_MUSIC

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        return frozenset({ProviderCapability.PLAYLIST_SYNC})

    @property
    def catalog(self):
        return None

    @property
    def library(self):
        return None

    @property
    def delivery(self):
        return None

    @property
    def playlist_read(self):
        return None

    @property
    def playlist_write(self):
        return _FakeWritePort()


class _PlanSyncBackend:
    def __init__(self) -> None:
        registry = ProviderGatewayRegistry()
        registry.register(_PlanningGateway())  # type: ignore[arg-type]
        self._registry = registry

    def plan_sync(self, params: dict[str, object]) -> dict[str, object]:
        local = ManagedPlaylistDetail(
            summary=ManagedPlaylistSummary(
                local_playlist_id="local-1",
                name="Demo",
                provider_id=ProviderId.APPLE_MUSIC,
                track_count=1,
                sync_status="pending",
            ),
            tracks=(
                ManagedPlaylistTrack(local_track_id="t1", artist="Kygo", title="Firestone"),
            ),
        )
        tracks = (RemotePlaylistTrack(remote_track_id="r1", artist="Kygo", title="Firestone", position=1),)
        remote = RemotePlaylistSnapshot(
            provider_id=ProviderId.APPLE_MUSIC,
            remote_playlist_id="remote-1",
            name="Demo",
            snapshot_at_iso="2026-07-09T12:00:00Z",
            tracks=tracks,
            track_count=1,
            checksum=remote_playlist_snapshot_checksum(tracks),
            source_kind="provider_library",
        )
        return plan_sync(
            self._registry,
            local_detail=local,
            remote_snapshot=remote,
            provider_id=ProviderId.APPLE_MUSIC,
            direction=SyncDirection(params.get("direction", SyncDirection.PULL_FROM_PROVIDER.value)),
            sync_mode=SyncMode(params.get("sync_mode", SyncMode.DRY_RUN.value)),
        )


class _ApplySyncBackend:
    def __init__(self, tmp_path: Path) -> None:
        registry = ProviderGatewayRegistry()
        registry.register(_PlanningGateway())  # type: ignore[arg-type]
        self._registry = registry
        self._provider = RepositoryProvider(
            playlists_path=tmp_path / "managed_playlists.json",
            snapshots_dir=tmp_path / "snapshots",
            sync_operations_path=tmp_path / "sync_operations.json",
        )
        local = ManagedPlaylistDetail(
            summary=ManagedPlaylistSummary(
                local_playlist_id="local-apply",
                name="Push Demo",
                provider_id=ProviderId.APPLE_MUSIC,
                track_count=1,
                sync_status="pending",
                playlist_version=1,
            ),
            tracks=(
                ManagedPlaylistTrack(
                    local_track_id="loc-1",
                    artist="Daft Punk",
                    title="One More Time",
                ),
            ),
        )
        self._provider.managed_playlist_repository().upsert(local)
        tracks: tuple[RemotePlaylistTrack, ...] = ()
        self._remote = RemotePlaylistSnapshot(
            provider_id=ProviderId.APPLE_MUSIC,
            remote_playlist_id="remote-target",
            name="Push Demo",
            snapshot_at_iso="2026-07-10T12:00:00Z",
            tracks=tracks,
            track_count=0,
            checksum=remote_playlist_snapshot_checksum(tracks),
            source_kind="provider_library",
        )

    def plan_sync(self, params: dict[str, object]) -> dict[str, object]:
        local = self._provider.managed_playlist_repository().get_playlist("local-apply")
        assert local is not None
        return plan_sync(
            self._registry,
            local_detail=local,
            remote_snapshot=self._remote,
            provider_id=ProviderId.APPLE_MUSIC,
            direction=SyncDirection.PUSH_TO_PROVIDER,
            sync_mode=SyncMode.APPEND_ONLY,
        )

    def apply_sync(self, params: dict[str, object]) -> dict[str, object]:
        return apply_sync(
            self._registry,
            self._provider,
            params=params,
            local_playlist_id="local-apply",
        )


def test_plan_sync_bridge_round_trip() -> None:
    bridge = JsonRpcEngineBridge(backend=_PlanSyncBackend())  # type: ignore[arg-type]
    messages = bridge.handle(
        {
            "id": "plan-1",
            "command": BridgeCommand.PLAN_SYNC.value,
            "params": {
                "provider_id": "apple_music",
                "direction": "pull_from_provider",
                "sync_mode": "dry_run",
                "local_playlist_id": "local-1",
            },
        }
    )
    assert messages[-1]["ok"] is True
    plan = messages[-1]["result"]["sync_plan"]
    assert plan["sync_mode"] == "dry_run"
    assert plan["summary"]["already_present"] == 1
    assert "plan_checksum" in messages[-1]["result"]


def test_apply_sync_bridge_round_trip(tmp_path: Path) -> None:
    backend = _ApplySyncBackend(tmp_path)
    bridge = JsonRpcEngineBridge(backend=backend)  # type: ignore[arg-type]

    plan_messages = bridge.handle(
        {
            "id": "plan-apply",
            "command": BridgeCommand.PLAN_SYNC.value,
            "params": {
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "append_only",
                "local_playlist_id": "local-apply",
            },
        }
    )
    assert plan_messages[-1]["ok"] is True
    plan_checksum = plan_messages[-1]["result"]["plan_checksum"]

    apply_messages = bridge.handle(
        {
            "id": "apply-1",
            "command": BridgeCommand.APPLY_SYNC.value,
            "params": {
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "append_only",
                "local_playlist_id": "local-apply",
                "plan_checksum": plan_checksum,
                "expected_local_playlist_version": 1,
                "expected_remote_snapshot_checksum": backend._remote.checksum,
                "remote_playlist": backend._remote.to_dict(),
            },
        }
    )
    assert apply_messages[-1]["ok"] is True
    payload = apply_messages[-1]["result"]["sync_apply"]
    assert payload["operation"]["status"] == "completed"
    assert payload["final_sync_status"] == "synced"
