from __future__ import annotations

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalArtist, CanonicalTrack
from playlist_builder.integration.apple_music.mapper import (
    apple_music_track_from_fields,
    canonical_candidate_from_apple_music_track,
    resolution_candidates_from_apple_music_tracks,
)
from playlist_builder.integration.apple_music.models import AppleMusicTrack


def test_apple_music_track_from_fields_rejects_missing_persistent_id():
    assert apple_music_track_from_fields(persistent_id="", artist="Kygo", title="Firestone") is None


def test_resolution_candidates_keep_persistent_id_provider_specific():
    track = AppleMusicTrack(persistent_id="PID123", artist="Kygo", title="Firestone", query="Firestone Kygo")
    candidates = resolution_candidates_from_apple_music_tracks([track])

    assert candidates[0].persistent_id == "PID123"
    assert candidates[0].artist == "Kygo"


def test_canonical_candidate_does_not_store_persistent_id_on_track():
    track = AppleMusicTrack(persistent_id="PID123", artist="Kygo", title="Firestone")
    candidate = canonical_candidate_from_apple_music_track(track, score=92.0)

    assert candidate.provider_hints == ("PID123",)
    assert candidate.track.isrc is None
    assert candidate.track.title == "Firestone"
    assert not hasattr(candidate.track, "persistent_id")


def test_canonical_track_never_contains_persistent_id():
    canonical = CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone")
    assert not any(field.name == "persistent_id" for field in canonical.__class__.__dataclass_fields__.values())
