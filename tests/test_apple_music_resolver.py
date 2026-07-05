from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.integration.apple_music.resolver import (
    AppleMusicResolutionStatus,
    AppleMusicResolver,
)


def _track() -> CanonicalTrack:
    return CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone")


def test_resolver_cache_hit_skips_applescript(tmp_path: Path):
    store = JsonCache(tmp_path / "identity.json")
    identity_cache = IdentityCache(store)
    track = _track()
    identity_cache.put_identity(
        track,
        provider_id=ProviderId.APPLE_MUSIC,
        external_id="PID-CACHED",
        confidence=95.0,
        resolved_at=datetime(2026, 6, 29, tzinfo=UTC),
    )
    applescript = MagicMock()
    resolver = AppleMusicResolver(applescript, identity_cache)

    outcome = resolver.resolve(track)

    assert outcome.status == AppleMusicResolutionStatus.RESOLVED
    assert outcome.persistent_id == "PID-CACHED"
    assert outcome.cache_hit is True
    assert outcome.trace.cache_hit is True
    applescript.collect_candidates_batch.assert_not_called()


def test_resolver_cache_miss_searches_and_persists(tmp_path: Path):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.return_value = [
        [AppleMusicTrack(persistent_id="PID123", artist="Kygo", title="Firestone", query="Firestone Kygo")]
    ]
    resolver = AppleMusicResolver(applescript, identity_cache)
    track = _track()

    outcome = resolver.resolve(track)

    assert outcome.status == AppleMusicResolutionStatus.RESOLVED
    assert outcome.persistent_id == "PID123"
    assert outcome.cache_hit is False
    assert outcome.score >= 55
    assert outcome.trace.accepted is not None
    stored = identity_cache.get(track, ProviderId.APPLE_MUSIC)
    assert stored is not None
    assert stored.external_id == "PID123"


def test_resolver_rejects_low_score_candidate_with_diagnostics(tmp_path: Path):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.return_value = [
        [AppleMusicTrack(persistent_id="PID-BAD", artist="Mariah Carey", title="Fantasy", query="Firestone")]
    ]
    resolver = AppleMusicResolver(applescript, identity_cache)

    track = _track()
    outcome = resolver.resolve(track)

    assert outcome.status == AppleMusicResolutionStatus.NOT_FOUND
    assert outcome.trace.candidate_count == 1
    assert outcome.trace.best_score > 0
    assert "Meilleur:" in outcome.error
    assert identity_cache.get(track, ProviderId.APPLE_MUSIC) is None


def test_resolver_picks_best_candidate_among_many(tmp_path: Path):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.return_value = [
        [
            AppleMusicTrack(persistent_id="PID-BAD", artist="Someone", title="Other", query="Firestone"),
            AppleMusicTrack(persistent_id="PID-GOOD", artist="Kygo", title="Firestone", query="Kygo Firestone"),
        ]
    ]
    resolver = AppleMusicResolver(applescript, identity_cache)

    outcome = resolver.resolve(_track())

    assert outcome.persistent_id == "PID-GOOD"


def test_resolver_returns_not_found_when_no_candidates_with_queries(tmp_path: Path):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.return_value = [[]]
    catalog = MagicMock()
    catalog.search.return_value = CanonicalSearchResponse(
        request=CanonicalSearchRequest(query="Kygo Firestone"),
        candidates=(
            CanonicalCandidate(
                track=_track(),
                source="apple_music_catalog",
                raw_confidence=90.0,
            ),
        ),
    )
    resolver = AppleMusicResolver(applescript, identity_cache, catalog=catalog)

    outcome = resolver.resolve(_track())

    assert outcome.status == AppleMusicResolutionStatus.NOT_FOUND
    assert outcome.trace.candidate_count == 0
    assert "Catalogue iTunes" in outcome.error
    catalog.search.assert_called_once()


def test_resolver_handles_applescript_error(tmp_path: Path):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = RuntimeError("Music not running")
    resolver = AppleMusicResolver(applescript, identity_cache)

    outcome = resolver.resolve(_track())

    assert outcome.status == AppleMusicResolutionStatus.ERROR
    assert "Music not running" in outcome.error


def test_resolver_batch_preserves_length_when_pending_slots_unresolved(tmp_path: Path):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.return_value = [[], []]
    resolver = AppleMusicResolver(applescript, identity_cache)

    outcomes = resolver.resolve_batch(
        [
            (_track(), "Main"),
            (CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="B"), "Main"),
        ]
    )

    assert len(outcomes) == 2
    assert outcomes[0].status == AppleMusicResolutionStatus.NOT_FOUND
    assert outcomes[1].status == AppleMusicResolutionStatus.NOT_FOUND
