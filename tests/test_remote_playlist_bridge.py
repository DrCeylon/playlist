from __future__ import annotations

import pytest

from playlist_builder.app.bridge_runtime.playlist_sync_plan import plan_sync, remote_snapshot_from_dict
from playlist_builder.app.bridge_runtime.remote_playlist import get_remote_playlist, list_remote_playlists
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.ui.bridge import BridgeCommand, JsonRpcEngineBridge
from playlist_builder.ui.bridge.errors import BridgeError
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import (
    RemotePlaylist,
    RemotePlaylistSnapshot,
    RemotePlaylistTrack,
    remote_playlist_snapshot_checksum,
)


class _FakeReadPort:
    def list_playlists(self, *, account_id: str | None = None) -> tuple[RemotePlaylist, ...]:
        return (
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="pl-42",
                name="Workout",
                track_count=1,
                snapshot_at_iso="2026-07-09T12:00:00Z",
            ),
        )

    def get_playlist(self, remote_playlist_id: str) -> RemotePlaylistSnapshot:
        tracks = (
            RemotePlaylistTrack(
                remote_track_id="t-1",
                artist="Kygo",
                title="Firestone",
                position=1,
            ),
        )
        return RemotePlaylistSnapshot(
            provider_id=ProviderId.APPLE_MUSIC,
            remote_playlist_id=remote_playlist_id,
            name="Workout",
            snapshot_at_iso="2026-07-09T12:00:00Z",
            tracks=tracks,
            track_count=1,
            checksum=remote_playlist_snapshot_checksum(tracks),
            source_kind="provider_library",
        )


class _FakeGateway:
    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.APPLE_MUSIC

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        return frozenset({ProviderCapability.PLAYLIST_LIBRARY_BROWSE})

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
    def playlist_read(self) -> _FakeReadPort:
        return _FakeReadPort()

    @property
    def playlist_write(self):
        return None


class _RemotePlaylistBackend:
    def __init__(self) -> None:
        registry = ProviderGatewayRegistry()
        registry.register(_FakeGateway())  # type: ignore[arg-type]
        self._registry = registry

    def list_remote_playlists(self, params: dict[str, object]) -> dict[str, object]:
        provider_id = ProviderId(str(params.get("provider_id", ProviderId.APPLE_MUSIC.value)))
        playlists = list_remote_playlists(self._registry, provider_id=provider_id)
        return {"remote_playlists": list(playlists)}

    def get_remote_playlist(self, params: dict[str, object]) -> dict[str, object]:
        provider_id = ProviderId(str(params.get("provider_id", ProviderId.APPLE_MUSIC.value)))
        remote_playlist_id = str(params.get("remote_playlist_id", ""))
        snapshot = get_remote_playlist(
            self._registry,
            provider_id=provider_id,
            remote_playlist_id=remote_playlist_id,
        )
        return {"remote_playlist": snapshot}


def test_list_remote_playlists_bridge_round_trip() -> None:
    bridge = JsonRpcEngineBridge(backend=_RemotePlaylistBackend())  # type: ignore[arg-type]
    messages = bridge.handle(
        {
            "id": "remote-1",
            "command": BridgeCommand.LIST_REMOTE_PLAYLISTS.value,
            "params": {"provider_id": "apple_music"},
        }
    )
    assert messages[-1]["ok"] is True
    playlists = messages[-1]["result"]["remote_playlists"]
    assert len(playlists) == 1
    assert playlists[0]["remote_playlist_id"] == "pl-42"
    assert playlists[0]["provider_id"] == "apple_music"


def test_get_remote_playlist_bridge_round_trip() -> None:
    bridge = JsonRpcEngineBridge(backend=_RemotePlaylistBackend())  # type: ignore[arg-type]
    messages = bridge.handle(
        {
            "id": "remote-2",
            "command": BridgeCommand.GET_REMOTE_PLAYLIST.value,
            "params": {
                "provider_id": "apple_music",
                "remote_playlist_id": "pl-42",
            },
        }
    )
    assert messages[-1]["ok"] is True
    snapshot = messages[-1]["result"]["remote_playlist"]
    assert snapshot["remote_playlist_id"] == "pl-42"
    assert snapshot["source_kind"] == "provider_library"
    assert len(snapshot["tracks"]) == 1
    assert snapshot["tracks"][0]["artist"] == "Kygo"


class _EmptyReadPort:
    def list_playlists(self, *, account_id: str | None = None) -> tuple[RemotePlaylist, ...]:
        return ()

    def get_playlist(self, remote_playlist_id: str) -> RemotePlaylistSnapshot:
        tracks: tuple[RemotePlaylistTrack, ...] = ()
        return RemotePlaylistSnapshot(
            provider_id=ProviderId.APPLE_MUSIC,
            remote_playlist_id=remote_playlist_id,
            name=remote_playlist_id,
            snapshot_at_iso="2026-07-09T12:00:00Z",
            tracks=tracks,
            track_count=0,
            checksum=remote_playlist_snapshot_checksum(tracks),
            source_kind="provider_library",
        )


class _NoCapabilityGateway:
    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.APPLE_MUSIC

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        return frozenset({ProviderCapability.CATALOG_SEARCH})

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


class _BrowseWithoutReadPortGateway:
    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.APPLE_MUSIC

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        return frozenset({ProviderCapability.PLAYLIST_LIBRARY_BROWSE})

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


class _EmptyReadGateway:
    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.APPLE_MUSIC

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        return frozenset({ProviderCapability.PLAYLIST_LIBRARY_BROWSE})

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
    def playlist_read(self) -> _EmptyReadPort:
        return _EmptyReadPort()

    @property
    def playlist_write(self):
        return None


def test_list_remote_playlists_empty() -> None:
    registry = ProviderGatewayRegistry()
    registry.register(_EmptyReadGateway())  # type: ignore[arg-type]
    playlists = list_remote_playlists(registry, provider_id=ProviderId.APPLE_MUSIC)
    assert playlists == ()


def test_get_remote_playlist_missing_playlist_returns_empty_snapshot() -> None:
    registry = ProviderGatewayRegistry()
    registry.register(_EmptyReadGateway())  # type: ignore[arg-type]
    snapshot = get_remote_playlist(registry, provider_id=ProviderId.APPLE_MUSIC, remote_playlist_id="missing-pl")
    assert snapshot["remote_playlist_id"] == "missing-pl"
    assert snapshot["tracks"] == []
    assert snapshot["track_count"] == 0


def test_list_remote_playlists_raises_when_provider_missing() -> None:
    registry = ProviderGatewayRegistry()
    with pytest.raises(BridgeError, match="n'est pas disponible"):
        list_remote_playlists(registry, provider_id=ProviderId.SPOTIFY)


def test_list_remote_playlists_raises_without_browse_capability() -> None:
    registry = ProviderGatewayRegistry()
    registry.register(_NoCapabilityGateway())  # type: ignore[arg-type]
    with pytest.raises(BridgeError, match="ne supporte pas la lecture"):
        list_remote_playlists(registry, provider_id=ProviderId.APPLE_MUSIC)


def test_list_remote_playlists_raises_when_read_port_missing() -> None:
    registry = ProviderGatewayRegistry()
    registry.register(_BrowseWithoutReadPortGateway())  # type: ignore[arg-type]
    with pytest.raises(BridgeError, match="port lecture playlist n'est pas configuré"):
        list_remote_playlists(registry, provider_id=ProviderId.APPLE_MUSIC)


def test_get_remote_playlist_requires_remote_playlist_id() -> None:
    registry = ProviderGatewayRegistry()
    registry.register(_FakeGateway())  # type: ignore[arg-type]
    with pytest.raises(BridgeError, match="remote_playlist_id est requis"):
        get_remote_playlist(registry, provider_id=ProviderId.APPLE_MUSIC, remote_playlist_id="  ")


def test_plan_sync_accepts_snapshot_from_remote_read_flow() -> None:
    registry = ProviderGatewayRegistry()
    registry.register(_FakeGateway())  # type: ignore[arg-type]
    snapshot_payload = get_remote_playlist(registry, provider_id=ProviderId.APPLE_MUSIC, remote_playlist_id="pl-42")
    snapshot = remote_snapshot_from_dict(snapshot_payload)
    local = ManagedPlaylistDetail(
        summary=ManagedPlaylistSummary(
            local_playlist_id="local-1",
            name="Workout",
            provider_id=ProviderId.APPLE_MUSIC,
            track_count=0,
            sync_status="pending",
        ),
        tracks=(),
    )
    result = plan_sync(
        registry,
        local_detail=local,
        remote_snapshot=snapshot,
        provider_id=ProviderId.APPLE_MUSIC,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.DRY_RUN,
    )
    plan = result["sync_plan"]
    assert plan["sync_mode"] == "dry_run"
    assert plan["summary"]["additions"] == 1
    assert plan["summary"]["already_present"] == 0
