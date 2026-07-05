"""Tests for playlist generation fulfillment."""

from unittest.mock import MagicMock

from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.core.models import TrackRef
from playlist_builder.discovery.fulfillment import (
    build_expansion_queries,
    explain_shortfall,
    max_discovery_queries_for,
)
from playlist_builder.discovery.itunes_provider import ITunesCandidateProvider
from playlist_builder.discovery.models import DiscoveryQuery
from playlist_builder.discovery.pipeline import DiscoveryPipeline
from playlist_builder.discovery.providers import StaticCandidateProvider
from playlist_builder.planning.models import (
    CandidateTrack,
    GenerationConstraints,
    PlaylistRequest,
    SeedTrack,
)
from playlist_builder.session.engine import GenerationSessionEngine


def _request(*, target: int = 20) -> PlaylistRequest:
    return PlaylistRequest(
        name="Test",
        seeds=(SeedTrack(TrackRef("Kygo", "Firestone")),),
        constraints=GenerationConstraints(target_track_count=target),
    )


def test_max_discovery_queries_scales_with_target():
    assert max_discovery_queries_for(_request(target=20)) >= 20
    assert max_discovery_queries_for(_request(target=5)) >= 12


def test_itunes_provider_uses_multiple_hits_per_query():
    catalog = MagicMock()
    catalog.search.return_value = CanonicalSearchResponse(
        request=CanonicalSearchRequest(query="Kygo", limit=5),
        candidates=(
            CanonicalCandidate(
                track=CanonicalTrack(artist=CanonicalArtist(name="A1"), title="T1"),
                source="itunes",
            ),
            CanonicalCandidate(
                track=CanonicalTrack(artist=CanonicalArtist(name="A2"), title="T2"),
                source="itunes",
            ),
        )
    )
    provider = ITunesCandidateProvider(catalog, per_query_limit=5)
    results = provider.discover(_request(), [DiscoveryQuery(term="Kygo", source="seed", weight=1.0)])
    assert len(results) == 2
    catalog.search.assert_called_once()


def test_expansion_queries_add_broader_terms():
    queries = build_expansion_queries(_request(), pass_index=0)
    assert any("Kygo" in query.term for query in queries)


def test_explain_shortfall_describes_gap():
    message = explain_shortfall(
        _request(),
        target=20,
        selected=3,
        discovered=8,
        eligible=5,
        rejected=2,
        passes_used=3,
    )
    assert "Demandé : 20" in message
    assert "Obtenu : 3" in message


def test_engine_reports_shortfall_when_catalog_is_small():
    static = StaticCandidateProvider(
        [
            CandidateTrack(track=TrackRef("Artist", f"Track {index}"), score=80.0, source="static")
            for index in range(3)
        ]
    )
    engine = GenerationSessionEngine(DiscoveryPipeline([static]))
    session = engine.generate(_request(target=20))
    generated = session.generated_playlist
    assert len(generated.candidates) == 4
    assert generated.is_short
    assert generated.shortfall_message
