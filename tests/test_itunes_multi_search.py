from __future__ import annotations

import json
from unittest.mock import patch

from playlist_builder.integration.apple_music.itunes_client import ITunesSearchClient
from playlist_builder.integration.apple_music.models import AppleITunesSearchHit


def test_search_artists_returns_multiple_hits() -> None:
    client = ITunesSearchClient()
    payload = {
        "results": [
            {"artistName": "Muse", "artistId": 1, "wrapperType": "artist"},
            {"artistName": "Muse UK", "artistId": 2, "wrapperType": "artist"},
        ]
    }

    with patch("playlist_builder.integration.apple_music.itunes_client.urllib.request.urlopen") as urlopen:
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps(payload).encode("utf-8")
        hits, error = client.search_artists("muse", limit=5)

    assert error == ""
    assert len(hits) == 2
    assert isinstance(hits[0], AppleITunesSearchHit)
    assert hits[0].artist_name == "Muse"


def test_search_tracks_returns_multiple_hits() -> None:
    client = ITunesSearchClient()
    payload = {
        "results": [
            {
                "artistName": "Kygo",
                "trackName": "Firestone",
                "trackId": 10,
                "collectionName": "Cloud Nine",
                "trackTimeMillis": 271000,
            },
            {
                "artistName": "Kygo",
                "trackName": "Stole the Show",
                "trackId": 11,
            },
        ]
    }

    with patch("playlist_builder.integration.apple_music.itunes_client.urllib.request.urlopen") as urlopen:
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps(payload).encode("utf-8")
        hits, error = client.search_tracks("fire", limit=5)

    assert error == ""
    assert len(hits) == 2
    assert hits[0].track_name == "Firestone"
