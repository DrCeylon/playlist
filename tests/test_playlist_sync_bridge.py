from __future__ import annotations

from playlist_builder.app.bridge_runtime.playlist_sync_plan import plan_sync
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.ui.bridge import BridgeCommand, JsonRpcEngineBridge
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack, remote_playlist_snapshot_checksum


class _PlanningGateway:
    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.SPOTIFY

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
        return None


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
                provider_id=ProviderId.SPOTIFY,
                track_count=1,
                sync_status="pending",
            ),
            tracks=(
                ManagedPlaylistTrack(local_track_id="t1", artist="Kygo", title="Firestone"),
            ),
        )
        tracks = (RemotePlaylistTrack(remote_track_id="r1", artist="Kygo", title="Firestone", position=1),)
        remote = RemotePlaylistSnapshot(
            provider_id=ProviderId.SPOTIFY,
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
            provider_id=ProviderId.SPOTIFY,
            direction=SyncDirection(params.get("direction", SyncDirection.PULL_FROM_PROVIDER.value)),
            sync_mode=SyncMode(params.get("sync_mode", SyncMode.DRY_RUN.value)),
        )


def test_plan_sync_bridge_round_trip() -> None:
    bridge = JsonRpcEngineBridge(backend=_PlanSyncBackend())  # type: ignore[arg-type]
    messages = bridge.handle(
        {
            "id": "plan-1",
            "command": BridgeCommand.PLAN_SYNC.value,
            "params": {
                "provider_id": "spotify",
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
