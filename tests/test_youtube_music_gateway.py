from __future__ import annotations

import json
from pathlib import Path

import pytest

from playlist_builder.app.bridge_runtime.provider_platform import (
    load_snapshot_from_file,
    provider_auth_status,
    provider_connect,
    provider_disconnect,
    provider_options_from_registry,
)
from playlist_builder.app.factory import build_app_context
from playlist_builder.app.playlist_library.import_remote import ImportRemotePlaylist
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.app.playlist_sync.engine import PlaylistSyncEngine
from playlist_builder.app.playlist_sync.plan_checksum import plan_checksum
from playlist_builder.app.settings import AppSettings
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.integration.youtube_music.auth import YouTubeMusicAuthPort
from playlist_builder.integration.youtube_music.experimental_guard import is_ytmusicapi_installed
from playlist_builder.integration.youtube_music.gateway import build_youtube_music_gateway
from playlist_builder.integration.youtube_music.secrets import assert_bridge_safe_mapping, sanitize_user_message
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import ProviderAuthState


class FakeYouTubeClient:
    def list_library_playlists(self) -> list[dict]:
        return [{"playlistId": "PL123", "title": "Favorites", "count": 1}]

    def get_playlist(self, playlist_id: str, *, limit: int | None = None) -> dict:
        del limit
        return {
            "title": "Public Mix",
            "tracks": [
                {
                    "videoId": "vid-1",
                    "title": "Track One",
                    "artists": [{"name": "Artist A"}],
                    "album": {"name": "Album A"},
                    "duration_seconds": 200,
                }
            ],
        }

    def search_songs(self, query: str, *, limit: int = 10) -> list[dict]:
        return [{"videoId": "vid-2", "title": "Search Hit", "artists": [{"name": "Artist B"}]}]


@pytest.fixture
def youtube_registry(tmp_path: Path, monkeypatch) -> ProviderGatewayRegistry:
    def _installed() -> bool:
        return True

    def _client(headers_path=None):
        return FakeYouTubeClient()

    for target in (
        "playlist_builder.integration.youtube_music.experimental_guard.is_ytmusicapi_installed",
        "playlist_builder.integration.youtube_music.auth.is_ytmusicapi_installed",
        "playlist_builder.integration.youtube_music.gateway.is_ytmusicapi_installed",
        "playlist_builder.integration.youtube_music.client.is_ytmusicapi_installed",
    ):
        monkeypatch.setattr(target, _installed)
    for target in (
        "playlist_builder.integration.youtube_music.client.build_youtube_music_client",
        "playlist_builder.integration.youtube_music.auth.build_youtube_music_client",
        "playlist_builder.integration.youtube_music.read_port.build_youtube_music_client",
    ):
        monkeypatch.setattr(target, _client)
    registry = ProviderGatewayRegistry()
    registry.register(build_youtube_music_gateway(auth_config_path=tmp_path / "youtube_auth.json"))
    return registry


def test_youtube_gateway_registered_on_app_context(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "playlist_builder.integration.youtube_music.experimental_guard.is_ytmusicapi_installed",
        lambda: False,
    )
    settings = AppSettings(provider_auth_dir=tmp_path / "provider_auth")
    context = build_app_context(settings)
    gateway = context.registry.get(ProviderId.YOUTUBE_MUSIC)
    assert gateway is not None
    assert ProviderCapability.EXPERIMENTAL in gateway.capabilities
    assert gateway.playlist_write is None
    assert ProviderCapability.PLAYLIST_SYNC not in gateway.capabilities


def test_youtube_dependency_absent_reports_experimental_unavailable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "playlist_builder.integration.youtube_music.experimental_guard.is_ytmusicapi_installed",
        lambda: False,
    )
    registry = ProviderGatewayRegistry()
    registry.register(build_youtube_music_gateway(auth_config_path=tmp_path / "youtube_auth.json"))
    options = provider_options_from_registry(registry)
    youtube = next(item for item in options if item.provider_id == ProviderId.YOUTUBE_MUSIC)
    assert youtube.is_available is False
    assert youtube.is_experimental is True
    assert "non installé" in youtube.unavailable_reason.lower()


def test_youtube_auth_connect_and_disconnect(tmp_path: Path, youtube_registry: ProviderGatewayRegistry) -> None:
    headers_path = tmp_path / "headers.json"
    headers_path.write_text(json.dumps({"Cookie": "test-cookie"}), encoding="utf-8")
    result = provider_connect(
        youtube_registry,
        provider_id=ProviderId.YOUTUBE_MUSIC,
        params={"headers_file_path": str(headers_path), "display_name": "Demo User"},
    )
    account = result["provider_account"]
    assert account["auth_state"] == ProviderAuthState.CONNECTED.value
    assert account["display_name"] == "Demo User"
    assert "Cookie" not in json.dumps(account)
    assert_bridge_safe_mapping(account)

    status = provider_auth_status(youtube_registry, provider_id=ProviderId.YOUTUBE_MUSIC)
    assert status["provider_account"]["auth_state"] == ProviderAuthState.CONNECTED.value

    disconnected = provider_disconnect(youtube_registry, provider_id=ProviderId.YOUTUBE_MUSIC)
    assert disconnected["provider_account"]["auth_state"] == ProviderAuthState.DISCONNECTED.value


def test_youtube_list_and_get_remote_playlist(tmp_path: Path, youtube_registry: ProviderGatewayRegistry) -> None:
    from playlist_builder.app.bridge_runtime.remote_playlist import get_remote_playlist, list_remote_playlists

    headers_path = tmp_path / "headers.json"
    headers_path.write_text(json.dumps({"Cookie": "test-cookie"}), encoding="utf-8")
    provider_connect(
        youtube_registry,
        provider_id=ProviderId.YOUTUBE_MUSIC,
        params={"headers_file_path": str(headers_path), "display_name": "Demo"},
    )

    playlists = list_remote_playlists(youtube_registry, provider_id=ProviderId.YOUTUBE_MUSIC)
    assert len(playlists) == 1
    assert playlists[0]["remote_playlist_id"] == "PL123"

    snapshot = get_remote_playlist(youtube_registry, provider_id=ProviderId.YOUTUBE_MUSIC, remote_playlist_id="PL999")
    assert snapshot["track_count"] == 1
    assert snapshot["tracks"][0]["title"] == "Track One"
    assert snapshot["checksum"]


def test_youtube_import_repository_and_plan_sync(tmp_path: Path, youtube_registry: ProviderGatewayRegistry) -> None:
    from playlist_builder.app.bridge_runtime.remote_playlist import get_remote_playlist

    snapshot_payload = get_remote_playlist(youtube_registry, provider_id=ProviderId.YOUTUBE_MUSIC, remote_playlist_id="PL999")
    repos = RepositoryProvider(
        playlists_path=tmp_path / "managed_playlists.json",
        snapshots_dir=tmp_path / "snapshots",
        sync_operations_path=tmp_path / "sync_operations.json",
    )
    from playlist_builder.app.bridge_runtime.playlist_sync_plan import remote_snapshot_from_dict

    snapshot = remote_snapshot_from_dict(snapshot_payload)
    detail = ImportRemotePlaylist(
        repos.managed_playlist_repository(),
        repos.snapshot_archive(),
    ).execute(snapshot)
    assert detail.summary.track_count == 1
    assert detail.summary.provider_id == ProviderId.YOUTUBE_MUSIC

    local = ManagedPlaylistDetail(
        summary=ManagedPlaylistSummary(
            local_playlist_id=detail.summary.local_playlist_id,
            name=detail.summary.name,
            provider_id=ProviderId.YOUTUBE_MUSIC,
            track_count=0,
            sync_status="pending",
        ),
        tracks=(),
    )
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=snapshot,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.DRY_RUN,
    )
    assert plan_checksum(plan)


def test_apply_sync_refused_without_write_capability(youtube_registry: ProviderGatewayRegistry, tmp_path: Path) -> None:
    from playlist_builder.app.playlist_sync.apply import ApplySyncPlaylist, ApplySyncRequest
    from playlist_builder.app.bridge_runtime.playlist_sync_plan import remote_snapshot_from_dict
    from playlist_builder.app.bridge_runtime.remote_playlist import get_remote_playlist

    snapshot = remote_snapshot_from_dict(
        get_remote_playlist(youtube_registry, provider_id=ProviderId.YOUTUBE_MUSIC, remote_playlist_id="PL999")
    )
    repos = RepositoryProvider(
        playlists_path=tmp_path / "managed_playlists.json",
        snapshots_dir=tmp_path / "snapshots",
        sync_operations_path=tmp_path / "sync_operations.json",
    )
    local = ImportRemotePlaylist(repos.managed_playlist_repository(), repos.snapshot_archive()).execute(snapshot)
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=snapshot,
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.APPEND_ONLY,
    )
    gateway = youtube_registry.get(ProviderId.YOUTUBE_MUSIC)
    assert gateway is not None
    use_case = ApplySyncPlaylist(
        playlist_repository=repos.managed_playlist_repository(),
        operation_repository=repos.sync_operation_repository(),
    )
    result = use_case.execute(
        ApplySyncRequest(
            local_playlist_id=local.summary.local_playlist_id,
            provider_id=ProviderId.YOUTUBE_MUSIC,
            direction=SyncDirection.PUSH_TO_PROVIDER,
            sync_mode=SyncMode.APPEND_ONLY,
            confirm_destructive=False,
            expected_local_playlist_version=local.summary.playlist_version,
            expected_remote_snapshot_checksum=snapshot.checksum,
            plan_checksum=plan_checksum(plan),
        ),
        local=local,
        remote=snapshot,
        write_port=gateway.playlist_write,
        provider_capabilities=gateway.capabilities,
    )
    assert result.operation.error_code in {
        "write_port_missing",
        "write_capability_missing",
        "provider_unavailable",
    }


def test_file_snapshot_fallback_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "demo.csv"
    csv_path.write_text("artist,title,album,position\nArtist,Title,Album,1\n", encoding="utf-8")
    payload = load_snapshot_from_file(
        {
            "file_path": str(csv_path),
            "provider_id": "youtube_music",
            "playlist_name": "CSV Demo",
        }
    )
    snapshot = payload["remote_playlist"]
    assert snapshot["track_count"] == 1
    assert snapshot["provider_id"] == "youtube_music"
    assert snapshot["tracks"][0]["artist"] == "Artist"


def test_sanitize_user_message_redacts_sensitive_fragments() -> None:
    raw = "SAPISID=abc123 Authorization: Bearer secret-token"
    cleaned = sanitize_user_message(raw)
    assert "secret-token" not in cleaned
    assert "SAPISID=abc123" not in cleaned


def test_real_ytmusicapi_dependency_optional() -> None:
    # CI/core install should not require ytmusicapi.
    assert isinstance(is_ytmusicapi_installed(), bool)
