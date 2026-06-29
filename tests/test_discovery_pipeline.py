from playlist_builder.core.models import TrackRef
from playlist_builder.discovery.models import CandidatePool
from playlist_builder.discovery.pipeline import DiscoveryPipeline
from playlist_builder.discovery.providers import StaticCandidateProvider
from playlist_builder.discovery.query_builder import build_discovery_queries
from playlist_builder.planning.models import (
    CandidateTrack,
    ConstraintKind,
    GenerationConstraints,
    InclusionRule,
    PlaylistRequest,
    SeedTrack,
)
from playlist_builder.session.engine import GenerationSessionEngine


def _request() -> PlaylistRequest:
    return PlaylistRequest(
        name="Zelda Adventure",
        seeds=(SeedTrack(TrackRef("Koji Kondo", "Gerudo Valley")),),
        constraints=GenerationConstraints(
            target_track_count=2,
            preferred_terms=("adventure",),
            inclusions=(InclusionRule(ConstraintKind.GENRE, "OST"),),
        ),
    )


def test_query_builder_uses_seeds_and_inclusions():
    queries = build_discovery_queries(_request())

    assert any(query.source == "seed" and "Gerudo Valley" in query.term for query in queries)
    assert any(query.source == "inclusion:genre" and query.term == "OST" for query in queries)


def test_candidate_pool_deduplicates_by_best_score():
    request = _request()
    low = CandidateTrack(TrackRef("A", "Same"), score=10)
    high = CandidateTrack(TrackRef("A", "Same"), score=80)

    pool = CandidatePool(request=request, candidates=(low, high)).deduplicated()

    assert pool.size == 1
    assert pool.candidates[0].score == 80


def test_discovery_pipeline_collects_provider_candidates():
    provider = StaticCandidateProvider([
        CandidateTrack(TrackRef("Koji Kondo", "Lost Woods"), score=80, genre="OST"),
    ])

    result = DiscoveryPipeline([provider]).discover(_request())

    assert result.candidate_count == 1
    assert result.provider_stats == {"static": 1}


def test_generation_session_engine_builds_full_session():
    provider = StaticCandidateProvider([
        CandidateTrack(TrackRef("Koji Kondo", "Lost Woods"), score=80, genre="OST", mood="adventure"),
        CandidateTrack(TrackRef("Koji Kondo", "Dragon Roost Island"), score=70, genre="OST", mood="adventure"),
    ])
    engine = GenerationSessionEngine(DiscoveryPipeline([provider]))

    session = engine.generate(_request())

    assert session.candidate_pool is not None
    assert session.analysis is not None
    assert session.generated_playlist.tracks == [
        TrackRef("Koji Kondo", "Lost Woods"),
        TrackRef("Koji Kondo", "Dragon Roost Island"),
    ]
    assert "Rapport du labo musical" in session.report
