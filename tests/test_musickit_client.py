from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.catalog.cache import JsonCache
from playlist_builder.catalog.scoring import MIN_MUSICKIT_MATCH_SCORE, pick_best_match, score_track_match
from playlist_builder.core.models import TrackAddResult, TrackAddStatus, TrackRef
from playlist_builder.music.musickit_client import MusicKitClient, MusicKitCredentials


def test_score_track_match_musickit_shape():
    item = {
        "attributes": {
            "artistName": "Kygo",
            "name": "Firestone",
        }
    }
    assert score_track_match("Kygo", "Firestone", item) == 100


def test_pick_best_match_musickit_rejects_partial_only():
    candidates = [
        {"attributes": {"artistName": "Kygo", "name": "Other Song"}},
        {"attributes": {"artistName": "Someone", "name": "Firestone"}},
    ]
    assert pick_best_match("Kygo", "Firestone", candidates, min_score=MIN_MUSICKIT_MATCH_SCORE) is None


def test_find_song_id_uses_cache(tmp_path):
    cache = JsonCache(tmp_path / "musickit.json")
    cache.set("musickit::us::kygo::firestone", {"song_id": "123", "error": ""})
    client = MusicKitClient(MusicKitCredentials("dev", "user"), storefront="us", cache=cache)

    track = TrackRef(artist="Kygo", title="Firestone")
    assert client.find_song_id(track) == ("123", "")


def test_create_or_update_playlist_skips_existing_without_api(tmp_path):
    track = TrackRef(artist="Kygo", title="Firestone")
    client = MusicKitClient(MusicKitCredentials("dev", "user"), storefront="us")

    with (
        patch.object(client, "find_library_playlist_id_by_name", return_value="pl.123"),
        patch.object(client, "load_library_playlist_keys", return_value={track.key}),
        patch.object(client, "find_song_id") as find_song_id,
        patch.object(client, "add_tracks_to_library_playlist") as add_tracks,
    ):
        results = client.create_or_update_playlist("Test", [track])

    find_song_id.assert_not_called()
    add_tracks.assert_not_called()
    assert results == [TrackAddResult(track=track, status=TrackAddStatus.SKIPPED)]


def test_create_or_update_playlist_creates_with_found_ids():
    tracks = [
        TrackRef(artist="Kygo", title="Firestone"),
        TrackRef(artist="Unknown", title="Missing"),
    ]
    client = MusicKitClient(MusicKitCredentials("dev", "user"), storefront="us")

    with (
        patch.object(client, "find_library_playlist_id_by_name", return_value=None),
        patch.object(client, "find_song_id", side_effect=[("song-1", ""), (None, "not found")]),
        patch.object(client, "create_library_playlist", return_value="pl.new") as create_playlist,
    ):
        results = client.create_or_update_playlist("Test", tracks, description="Pool party")

    create_playlist.assert_called_once_with("Test", "Pool party", ["song-1"])
    assert results[0].status == TrackAddStatus.ADDED
    assert results[1].status == TrackAddStatus.NOT_FOUND


def test_credentials_from_env_missing(monkeypatch):
    monkeypatch.delenv("APPLE_MUSIC_DEVELOPER_TOKEN", raising=False)
    monkeypatch.delenv("APPLE_MUSIC_USER_TOKEN", raising=False)
    with pytest.raises(Exception):
        MusicKitCredentials.from_env()
