from __future__ import annotations

from unittest.mock import MagicMock

from playlist_builder.integration.apple_music.delivery_pacing import (
    wait_for_playlist_cleared,
    wait_for_playlist_track_count,
)


def test_wait_for_playlist_track_count_succeeds_when_count_reached():
    applescript = MagicMock()
    applescript.count_playlist_tracks.side_effect = [0, 1, 3]

    assert wait_for_playlist_track_count(
        applescript,
        "Demo",
        minimum_count=3,
        timeout_seconds=2.0,
        poll_seconds=0.01,
    )
    assert applescript.count_playlist_tracks.call_count >= 3


def test_wait_for_playlist_cleared_succeeds_when_empty():
    applescript = MagicMock()
    applescript.count_playlist_tracks.side_effect = [2, 1, 0]

    assert wait_for_playlist_cleared(
        applescript,
        "Demo",
        timeout_seconds=2.0,
        poll_seconds=0.01,
    )


def test_wait_for_playlist_track_count_times_out():
    applescript = MagicMock()
    applescript.count_playlist_tracks.return_value = 0

    assert not wait_for_playlist_track_count(
        applescript,
        "Demo",
        minimum_count=2,
        timeout_seconds=0.05,
        poll_seconds=0.02,
    )
