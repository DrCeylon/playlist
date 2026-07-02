from __future__ import annotations

import pytest

from playlist_builder.catalog.scoring import MIN_MATCH_SCORE, pick_best_match, score_track_match
from playlist_builder.core.applescript import apple_escape, format_applescript_error
from playlist_builder.playlists.loader import PlaylistValidationError, load_playlist


def test_score_track_match_exact():
    item = {"artistName": "Kygo", "trackName": "Firestone"}
    assert score_track_match("Kygo", "Firestone", item) == 100


def test_score_track_match_partial():
    item = {"artistName": "Mark Ronson feat. Bruno Mars", "trackName": "Uptown Funk"}
    assert score_track_match("Mark Ronson", "Uptown Funk", item) == 100


def test_pick_best_match_rejects_low_confidence():
    results = [{"artistName": "Unknown Artist", "trackName": "Random Song"}]
    assert pick_best_match("Kygo", "Firestone", results) is None


def test_pick_best_match_returns_best_above_threshold():
    results = [
        {"artistName": "Someone Else", "trackName": "Other"},
        {"artistName": "Kygo", "trackName": "Firestone"},
    ]
    best = pick_best_match("Kygo", "Firestone", results)
    assert best is not None
    assert best["trackName"] == "Firestone"


def test_apple_escape_handles_special_characters():
    assert apple_escape('Say "Hello"\n') == 'Say \\"Hello\\"\\n'


def test_format_applescript_error_surfaces_automation_permission():
    message = format_applescript_error(
        'execution error: Not authorized to send Apple events to Music. (-1743)'
    )
    assert "Automatisation" in message
    assert "Réglages Système" in message


def test_load_playlist_valid(tmp_path):
    path = tmp_path / "playlist.json"
    path.write_text(
        """
        {
          "name": "Test Playlist",
          "sections": [
            {
              "name": "Main",
              "songs": [{"artist": "Kygo", "title": "Firestone"}]
            }
          ]
        }
        """,
        encoding="utf-8",
    )
    playlist = load_playlist(path)
    assert playlist.name == "Test Playlist"
    assert len(playlist.tracks) == 1
    assert len(playlist.sections) == 1
    assert playlist.sections[0].name == "Main"
    assert playlist.tracks[0].key == "kygo::firestone"


def test_load_playlist_preserves_section_track_order(tmp_path):
    path = tmp_path / "playlist.json"
    path.write_text(
        """
        {
          "name": "Ordered",
          "sections": [
            {
              "name": "A",
              "songs": [
                {"artist": "A1", "title": "One"},
                {"artist": "A2", "title": "Two"}
              ]
            },
            {
              "name": "B",
              "songs": [{"artist": "B1", "title": "Three"}]
            }
          ]
        }
        """,
        encoding="utf-8",
    )
    playlist = load_playlist(path)
    assert [track.label for track in playlist.tracks] == [
        "A1 - One",
        "A2 - Two",
        "B1 - Three",
    ]
    assert [section.name for section in playlist.sections] == ["A", "B"]
    assert [track.section for track in playlist.tracks] == ["A", "A", "B"]


def test_load_playlist_missing_field(tmp_path):
    path = tmp_path / "playlist.json"
    path.write_text(
        '{"name": "Test", "sections": [{"name": "Main", "songs": [{"artist": "Kygo"}]}]}',
        encoding="utf-8",
    )
    with pytest.raises(PlaylistValidationError):
        load_playlist(path)
