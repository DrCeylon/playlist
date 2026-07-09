from __future__ import annotations

import ast
from pathlib import Path

import pytest

from playlist_builder.canonical.contracts import ProviderGateway
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.apple_music.gateway import build_default_registry
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.integration.ports.provider_auth import ProviderAuthPort
from playlist_builder.ui.shared.dto.remote_playlist import (
    ProviderAuthState,
    RemotePlaylist,
    RemotePlaylistSnapshot,
    RemotePlaylistTrack,
)


class _FakePlaylistReadPort:
    def list_playlists(self, *, account_id: str | None = None) -> tuple[RemotePlaylist, ...]:
        return (
            RemotePlaylist(
                provider_id=ProviderId.SPOTIFY,
                remote_playlist_id="pl-1",
                name="Favorites",
                track_count=2,
            ),
        )

    def get_playlist(self, remote_playlist_id: str) -> RemotePlaylistSnapshot:
        return RemotePlaylistSnapshot(
            provider_id=ProviderId.SPOTIFY,
            remote_playlist_id=remote_playlist_id,
            name="Favorites",
            snapshot_at_iso="2026-07-09T12:00:00Z",
            tracks=(
                RemotePlaylistTrack(remote_track_id="t1", artist="A", title="B", position=1),
            ),
            track_count=1,
            checksum="abc",
            source_kind="provider_library",
        )


class _FakePlaylistWritePort:
    def create_playlist(self, name: str) -> str:
        return "new-pl"

    def upsert_tracks(self, remote_playlist_id: str, tracks: tuple[RemotePlaylistTrack, ...]) -> None:
        return None

    def remove_tracks(self, remote_playlist_id: str, remote_track_ids: tuple[str, ...]) -> None:
        return None


class _FakeAuthPort:
    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.SPOTIFY

    def auth_state(self) -> ProviderAuthState:
        return ProviderAuthState.CONNECTED

    def connect(self, *, params: dict[str, str]) -> ProviderAuthState:
        return ProviderAuthState.CONNECTED

    def disconnect(self) -> ProviderAuthState:
        return ProviderAuthState.DISCONNECTED


class _PlaylistCapableGateway:
    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.SPOTIFY

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        return frozenset(
            {
                ProviderCapability.PLAYLIST_LIBRARY_BROWSE,
                ProviderCapability.PLAYLIST_SYNC,
            }
        )

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
    def playlist_read(self) -> _FakePlaylistReadPort:
        return _FakePlaylistReadPort()

    @property
    def playlist_write(self) -> _FakePlaylistWritePort:
        return _FakePlaylistWritePort()


def test_provider_playlist_ports_are_runtime_checkable() -> None:
    read_port = _FakePlaylistReadPort()
    write_port = _FakePlaylistWritePort()
    auth_port = _FakeAuthPort()
    assert isinstance(read_port, ProviderPlaylistReadPort)
    assert isinstance(write_port, ProviderPlaylistWritePort)
    assert isinstance(auth_port, ProviderAuthPort)


def test_provider_gateway_exposes_optional_playlist_ports() -> None:
    gateway = _PlaylistCapableGateway()
    assert isinstance(gateway, ProviderGateway)
    read_port = gateway.playlist_read
    write_port = gateway.playlist_write
    assert read_port is not None
    assert write_port is not None
    assert isinstance(read_port, ProviderPlaylistReadPort)
    assert isinstance(write_port, ProviderPlaylistWritePort)
    playlists = read_port.list_playlists()
    assert playlists[0].name == "Favorites"


def test_apple_music_gateway_has_no_playlist_ports_yet(tmp_path) -> None:
    registry = build_default_registry(identity_cache_path=tmp_path / "identity.json")
    gateway = registry.require(ProviderId.APPLE_MUSIC)
    assert gateway.playlist_read is None
    assert gateway.playlist_write is None


def test_capability_gating_requires_port_when_browse_declared() -> None:
    gateway = _PlaylistCapableGateway()
    assert ProviderCapability.PLAYLIST_LIBRARY_BROWSE in gateway.capabilities
    assert gateway.playlist_read is not None


def test_integration_ports_package_is_provider_neutral() -> None:
    ports_root = Path(__file__).resolve().parents[1] / "playlist_builder" / "integration" / "ports"
    forbidden = ("apple_music", "youtube", "ytmusic", "spotipy")
    offenders: list[str] = []
    for path in ports_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(token in alias.name for token in forbidden):
                        offenders.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if any(token in node.module for token in forbidden):
                    offenders.append(f"{path.name}: from {node.module}")
    assert offenders == []
