from __future__ import annotations

from playlist_builder.music.client import MusicClient


def test_normalize_key():
    assert MusicClient._normalize_key("Kygo::Firestone") == "kygo::firestone"
