from __future__ import annotations

from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalTrack,
)
from playlist_builder.integration.apple_music.catalog_ids import (
    catalog_track_id_from_candidate,
    catalog_url_from_candidate,
)


def _candidate(*hints: str) -> CanonicalCandidate:
    return CanonicalCandidate(
        track=CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone"),
        source="apple_music_catalog",
        provider_hints=hints,
        raw_confidence=100.0,
    )


def test_catalog_url_from_candidate_prefers_http_hint():
    candidate = _candidate(
        "https://music.apple.com/us/song/firestone/950274258",
        "itunes_track_id:950274258",
    )
    assert catalog_url_from_candidate(candidate) == "https://music.apple.com/us/song/firestone/950274258"


def test_catalog_track_id_from_hint():
    candidate = _candidate(
        "https://music.apple.com/us/song/firestone/950274258",
        "itunes_track_id:950274258",
    )
    assert catalog_track_id_from_candidate(candidate) == "950274258"


def test_catalog_track_id_from_url_when_hint_missing():
    candidate = _candidate("https://music.apple.com/us/song/firestone/950274258")
    assert catalog_track_id_from_candidate(candidate) == "950274258"
