from __future__ import annotations

from playlist_builder.app.bridge_runtime.remote_playlist import get_remote_playlist, list_remote_playlists
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.ui.bridge import BridgeCommand, JsonRpcEngineBridge
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
