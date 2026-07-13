from __future__ import annotations

import json
from pathlib import Path

import pytest

from playlist_builder.app.bridge_runtime.provider_platform import provider_connect
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalArtist, CanonicalPlaylist, CanonicalPlaylistSection, CanonicalTrack
from playlist_builder.integration.youtube_music.auth import YouTubeMusicAuthPort
from playlist_builder.integration.youtube_music.import_service import YouTubeMusicImportService
from playlist_builder.integration.youtube_music.playlist_write_port import YouTubeMusicPlaylistWritePort
from playlist_builder.integration.youtube_music.provider_import_port import YouTubeMusicProviderImportPort
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistTrack


class FakeWriteClient:
    def __init__(self) -> None:
        self.created: list[str] = []
        self.added: list[tuple[str, list[str]]] = []

    def list_library_playlists(self) -> list[dict]:
        return []

    def get_playlist(self, playlist_id: str, *, limit: int | None = None) -> dict:
        del playlist_id, limit
        return {"title": "Demo", "tracks": []}

    def search_songs(self, query: str, *, limit: int = 10) -> list[dict]:
        del limit
        return [{"videoId": f"vid-{query}", "title": query, "artists": [{"name": "Artist"}]}]

    def create_playlist(self, title: str, *, description: str = "") -> str:
        del description
        self.created.append(title)
        return "PL-created"

    def add_playlist_items(self, playlist_id: str, video_ids: list[str]) -> None:
        self.added.append((playlist_id, list(video_ids)))

    def remove_playlist_items(self, playlist_id: str, video_ids: list[str]) -> None:
        del playlist_id, video_ids


@pytest.fixture
def connected_auth(tmp_path: Path, monkeypatch) -> YouTubeMusicAuthPort:
    headers_path = tmp_path / "headers.json"
    headers_path.write_text(json.dumps({"Cookie": "demo"}), encoding="utf-8")
    monkeypatch.setattr(
        "playlist_builder.integration.youtube_music.experimental_guard.is_ytmusicapi_installed",
        lambda: True,
    )
    monkeypatch.setattr(
        "playlist_builder.integration.youtube_music.auth.is_ytmusicapi_installed",
        lambda: True,
    )
    for target in (
        "playlist_builder.integration.youtube_music.client.build_youtube_music_client",
        "playlist_builder.integration.youtube_music.resolver.build_youtube_music_client",
        "playlist_builder.integration.youtube_music.delivery.build_youtube_music_client",
        "playlist_builder.integration.youtube_music.playlist_write_port.build_youtube_music_client",
    ):
        monkeypatch.setattr(target, lambda headers_path=None: FakeWriteClient())
    auth = YouTubeMusicAuthPort(tmp_path / "youtube_auth.json")
    auth.connect(params={"headers_file_path": str(headers_path), "display_name": "Demo"})
    return auth


def test_youtube_write_port_creates_and_upserts_tracks(connected_auth: YouTubeMusicAuthPort) -> None:
    write_port = YouTubeMusicPlaylistWritePort(connected_auth)
    playlist_id = write_port.create_playlist("Parity Demo")
    assert playlist_id == "PL-created"
    write_port.upsert_tracks(
        playlist_id,
        (
            RemotePlaylistTrack(
                remote_track_id="vid-1",
                artist="Artist",
                title="Track",
                album="",
                duration_ms=0,
                position=1,
            ),
        ),
    )


def test_youtube_provider_import_port_resolves_and_delivers(connected_auth: YouTubeMusicAuthPort) -> None:
    import_service = YouTubeMusicImportService(connected_auth, catalog=None)
    import_port = YouTubeMusicProviderImportPort(import_service)
    track = CanonicalTrack(artist=CanonicalArtist(name="Artist A"), title="Track One")
    outcome = import_port.resolve(track)
    assert outcome.status.value == "resolved"
    playlist = CanonicalPlaylist(
        name="YouTube Import",
        sections=(CanonicalPlaylistSection(name="Main", tracks=(track,)),),
    )
    report = import_port.deliver_playlist(playlist, [outcome])
    assert any(result.status.value == "added" for result in report.results)
