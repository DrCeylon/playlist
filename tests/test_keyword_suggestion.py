from __future__ import annotations

from playlist_builder.ui.shared.autocomplete.keyword_suggestion import suggest_keywords


def test_suggest_keywords_from_track_metadata():
    keywords = suggest_keywords(
        artist_name="Calvin Harris",
        track_title="Summer",
        album_title="Motion",
        release_year=2014,
        primary_genre_name="Dance",
    )

    assert "dance" in keywords
    assert "summer" in keywords
    assert "2010s" in keywords


def test_suggest_keywords_deduplicates_and_limits():
    keywords = suggest_keywords(
        artist_name="Muse",
        track_title="Butterflies & Hurricanes",
        album_title="Absolution",
        release_year=2003,
        primary_genre_name="Alternative Rock",
    )

    assert len(keywords) == len(set(keywords))
    assert len(keywords) <= 8
    assert "alternative" in keywords
    assert "2000s" in keywords


def test_suggest_keywords_preserves_manual_signal_when_sparse():
    keywords = suggest_keywords(artist_name="Kygo", track_title="Firestone")

    assert keywords
    assert "firestone" in keywords or "kygo" in keywords
