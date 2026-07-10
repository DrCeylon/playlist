from __future__ import annotations

"""Bridge journey test harness.

Isolation (per ``tmp_path`` fixture):
- ``data/managed_playlists.json``, ``data/snapshots/``, ``data/sync_operations.json``
- ``data/provider_auth/``, ``data/history/sessions.json``
- ``cache/catalog.json``, ``cache/identity.json``

Mocks — no Music.app, no network, no real accounts:
- ``FakeSyncGateway`` replaces Apple Music for sync (``ProviderPlaylistWritePort`` via ``FakeWritePort``)
- ``YouTubeMusicProviderGateway`` registered for capability listing only (no API calls in these tests)

Determinism:
- Fixed ISO timestamps and checksums in ``sample_remote_playlist_dict``
- ``reset_default_bus()`` before each harness build
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playlist_builder.app.bridge_runtime.backend import RuntimeEngineBridgeBackend
from playlist_builder.app.factory import AppContext
from playlist_builder.app.settings import AppSettings
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.integration.gateway.service import IntegrationGateway
from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.observability import reset_default_bus
from playlist_builder.ui.bridge import JsonRpcEngineBridge
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistTrack
from playlist_builder.ui.shared.history import SessionHistoryRepository, SessionHistoryService


class FakeWritePort(ProviderPlaylistWritePort):
    """Deterministic write port — records calls, simulates failures, no I/O."""

    def __init__(self, *, fail_on_call: int | None = None) -> None:
        self.upserted: list[tuple[str, tuple[RemotePlaylistTrack, ...]]] = []
        self.removed: list[tuple[str, tuple[str, ...]]] = []
        self._fail_on_call = fail_on_call
        self._call_count = 0

    def create_playlist(self, name: str) -> str:
        return "remote-target"

    def upsert_tracks(self, remote_playlist_id: str, tracks: tuple[RemotePlaylistTrack, ...]) -> None:
        self._call_count += 1
        if self._fail_on_call is not None and self._call_count >= self._fail_on_call:
            raise RuntimeError("simulated write failure")
        self.upserted.append((remote_playlist_id, tracks))

    def remove_tracks(self, remote_playlist_id: str, remote_track_ids: tuple[str, ...]) -> None:
        self._call_count += 1
        if self._fail_on_call is not None and self._call_count >= self._fail_on_call:
            raise RuntimeError("simulated write failure")
        self.removed.append((remote_playlist_id, remote_track_ids))


class FakeSyncGateway:
    """Minimal Apple Music stand-in for sync bridge tests."""

    provider_id = ProviderId.APPLE_MUSIC
    capabilities = frozenset(
        {
            ProviderCapability.PLAYLIST_SYNC,
            ProviderCapability.PLAYLIST_LIBRARY_BROWSE,
        }
    )

    def __init__(self, write_port: FakeWritePort | None = None) -> None:
        self._write_port = write_port or FakeWritePort()

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
    def playlist_write(self) -> FakeWritePort:
        return self._write_port


@dataclass
class E2EHarness:
    tmp_path: Path
    settings: AppSettings
    context: AppContext
    provider: RepositoryProvider
    backend: RuntimeEngineBridgeBackend
    bridge: JsonRpcEngineBridge
    write_port: FakeWritePort

    def call(self, command: str, params: dict[str, Any] | None = None, *, request_id: str = "e2e-req") -> list[dict[str, Any]]:
        return self.bridge.handle(
            {
                "id": request_id,
                "command": command,
                "params": params or {},
            }
        )

    def last_result(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        final = messages[-1]
        assert final.get("ok") is True, final
        return final["result"]

    def sync_apply(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return self.last_result(messages)["sync_apply"]


def build_e2e_harness(tmp_path: Path, *, write_port: FakeWritePort | None = None) -> E2EHarness:
    """Isolated harness — tmp paths only, fake sync gateway, reset observability bus."""
    reset_default_bus()
    settings = AppSettings(
        catalog_cache_path=tmp_path / "cache" / "catalog.json",
        identity_cache_path=tmp_path / "cache" / "identity.json",
        managed_playlists_path=tmp_path / "data" / "managed_playlists.json",
        playlist_snapshots_dir=tmp_path / "data" / "snapshots",
        sync_operations_path=tmp_path / "data" / "sync_operations.json",
        provider_auth_dir=tmp_path / "data" / "provider_auth",
        use_catalog_cache=False,
    )
    port = write_port or FakeWritePort()
    registry = ProviderGatewayRegistry()
    registry.register(FakeSyncGateway(port))  # type: ignore[arg-type]
    from playlist_builder.integration.youtube_music.gateway import build_youtube_music_gateway

    registry.register(build_youtube_music_gateway(auth_config_path=settings.provider_auth_dir / "youtube_music.json"))
    context = AppContext(
        settings=settings,
        registry=registry,
        gateway=IntegrationGateway(registry),
    )
    provider = RepositoryProvider(
        playlists_path=settings.managed_playlists_path,
        snapshots_dir=settings.playlist_snapshots_dir,
        sync_operations_path=settings.sync_operations_path,
    )
    backend = RuntimeEngineBridgeBackend(context)
    backend._repository_provider = provider
    backend._history = SessionHistoryService(
        SessionHistoryRepository(tmp_path / "data" / "history" / "sessions.json")
    )
    return E2EHarness(
        tmp_path=tmp_path,
        settings=settings,
        context=context,
        provider=provider,
        backend=backend,
        bridge=JsonRpcEngineBridge(backend=backend),
        write_port=port,
    )


def sample_remote_playlist_dict(*, checksum: str = "deadbeefcafebabe") -> dict[str, Any]:
    return {
        "provider_id": "apple_music",
        "remote_playlist_id": "remote-e2e-1",
        "name": "E2E Remote",
        "snapshot_at_iso": "2026-07-10T12:00:00",
        "track_count": 1,
        "checksum": checksum,
        "source_kind": "provider_library",
        "tracks": [
            {
                "remote_track_id": "r1",
                "artist": "Kygo",
                "title": "Firestone",
                "position": 0,
            },
        ],
    }
