from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.constants import FIELD_DELIMITER, RESULT_DELIMITER
from playlist_builder.integration.apple_music.gateway import build_default_registry
from playlist_builder.integration.apple_music.playlist_read_port import AppleMusicPlaylistReadPort
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistTrack, remote_playlist_snapshot_checksum


def test_parse_user_playlist_rows() -> None:
    row = f"12345{FIELD_DELIMITER}Road Trip{FIELD_DELIMITER}12"
    rows = AppleScriptClient._parse_user_playlist_rows(row)
    assert rows == [("12345", "Road Trip", 12)]


def test_parse_playlist_track_rows_converts_duration_to_ms() -> None:
    row = f"pid-1{FIELD_DELIMITER}Kygo{FIELD_DELIMITER}Firestone{FIELD_DELIMITER}Cloud Nine{FIELD_DELIMITER}245{FIELD_DELIMITER}1"
    rows = AppleScriptClient._parse_playlist_track_rows(row)
    assert rows == [("pid-1", "Kygo", "Firestone", "Cloud Nine", 245_000, 1)]


def test_apple_music_playlist_read_port_maps_list_and_snapshot() -> None:
    applescript = MagicMock()
    applescript.list_user_playlists.return_value = [
        ("pl-1", "Chill Mix", 2),
    ]
    applescript.load_playlist_tracks_by_id.return_value = [
        ("t-1", "Artist A", "Song A", "Album A", 180_000, 1),
        ("t-2", "Artist B", "Song B", "", 200_000, 2),
    ]
    port = AppleMusicPlaylistReadPort(applescript)

    playlists = port.list_playlists()
    assert len(playlists) == 1
    assert playlists[0].provider_id == ProviderId.APPLE_MUSIC
    assert playlists[0].remote_playlist_id == "pl-1"
    assert playlists[0].track_count == 2

    snapshot = port.get_playlist("pl-1")
    assert snapshot.remote_playlist_id == "pl-1"
    assert snapshot.name == "Chill Mix"
    assert snapshot.source_kind == "provider_library"
    assert len(snapshot.tracks) == 2
    assert snapshot.checksum == remote_playlist_snapshot_checksum(snapshot.tracks)
    applescript.load_playlist_tracks_by_id.assert_called_once_with("pl-1")


def test_apple_music_gateway_exposes_read_port_without_write(tmp_path) -> None:
    registry = build_default_registry(identity_cache_path=tmp_path / "identity.json")
    gateway = registry.require(ProviderId.APPLE_MUSIC)
    assert ProviderCapability.PLAYLIST_LIBRARY_BROWSE in gateway.capabilities
    assert isinstance(gateway.playlist_read, ProviderPlaylistReadPort)
    assert gateway.playlist_write is None


def test_get_playlist_requires_remote_playlist_id() -> None:
    port = AppleMusicPlaylistReadPort(MagicMock())
    with pytest.raises(ValueError, match="remote_playlist_id"):
        port.get_playlist("  ")


def test_parse_user_playlist_rows_preserves_special_characters() -> None:
    row = f"pl-1{FIELD_DELIMITER}Soirée « Chill » & Co.{FIELD_DELIMITER}3"
    rows = AppleScriptClient._parse_user_playlist_rows(row)
    assert rows == [("pl-1", "Soirée « Chill » & Co.", 3)]


def test_parse_playlist_track_rows_preserves_stable_positions() -> None:
    row_a = f"t-2{FIELD_DELIMITER}Björk{FIELD_DELIMITER}Hyperballad{FIELD_DELIMITER}Post{FIELD_DELIMITER}300{FIELD_DELIMITER}2"
    row_b = f"t-1{FIELD_DELIMITER}Björk{FIELD_DELIMITER}Army of Me{FIELD_DELIMITER}Post{FIELD_DELIMITER}240{FIELD_DELIMITER}1"
    rows = AppleScriptClient._parse_playlist_track_rows(f"{row_b}{RESULT_DELIMITER}{row_a}")
    assert [position for *_, position in rows] == [1, 2]
    assert rows[0][1:] == ("Björk", "Army of Me", "Post", 240_000, 1)
    assert rows[1][1:] == ("Björk", "Hyperballad", "Post", 300_000, 2)


def test_remote_playlist_snapshot_checksum_is_deterministic() -> None:
    tracks = (
        RemotePlaylistTrack(remote_track_id="t-1", artist="Kygo", title="Firestone", position=1),
        RemotePlaylistTrack(remote_track_id="t-2", artist="Avicii", title="Levels", position=2),
    )
    first = remote_playlist_snapshot_checksum(tracks)
    second = remote_playlist_snapshot_checksum(tracks)
    assert first == second
    assert len(first) == 16
