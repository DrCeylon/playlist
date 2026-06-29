from unittest.mock import MagicMock

from playlist_builder.core.models import CatalogMatch, TrackRef
from playlist_builder.discovery.itunes_provider import ITunesCandidateProvider, candidate_from_itunes_match
from playlist_builder.discovery.models import CandidatePool, DiscoveryQuery
from playlist_builder.discovery.pipeline import DiscoveryPipeline
from playlist_builder.discovery.probe import wanted_match_fields
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
from playlist_builder.session.engine import GenerationSessionEngine, merge_candidate_lists


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
    assert any(query.term == "OST" for query in queries)


def test_query_builder_dedupes_identical_terms():
    request = PlaylistRequest(
        name="Dedup",
        seeds=(SeedTrack(TrackRef("Kygo", "Firestone")),),
        constraints=GenerationConstraints(
            target_track_count=1,
            preferred_terms=("Kygo",),
            inclusions=(InclusionRule(ConstraintKind.ARTIST, "Kygo", weight=1.5),),
        ),
    )

    queries = build_discovery_queries(request)
    kygo_terms = [query for query in queries if query.term.lower() == "kygo"]

    assert len(kygo_terms) == 1
    assert kygo_terms[0].weight == 1.5


def test_wanted_match_fields_for_seed_label():
    query = DiscoveryQuery(term="Koji Kondo - Gerudo Valley", source="seed", weight=1.0)
    assert wanted_match_fields(query) == ("Koji Kondo", "Gerudo Valley")


def test_candidate_from_itunes_match_maps_metadata():
    query = DiscoveryQuery(term="OST", source="inclusion:genre", weight=1.0)
    match = CatalogMatch(
        query=TrackRef("Koji Kondo", "Gerudo Valley"),
        matched_artist="Koji Kondo",
        matched_title="Gerudo Valley",
        url="https://music.apple.com/example",
        raw={
            "primaryGenreName": "Soundtrack",
            "collectionName": "Ocarina of Time",
            "trackExplicitness": "notExplicit",
        },
    )

    candidate = candidate_from_itunes_match(match, query=query)

    assert candidate.genre == "Soundtrack"
    assert candidate.album == "Ocarina of Time"
    assert candidate.explicit is False


def test_itunes_provider_uses_search_term_and_metadata():
    search = MagicMock()
    search.search_term.return_value = CatalogMatch(
        query=TrackRef("Koji Kondo", "Gerudo Valley"),
        matched_artist="Koji Kondo",
        matched_title="Gerudo Valley",
        url="https://music.apple.com/example",
        raw={"primaryGenreName": "Soundtrack", "collectionName": "Zelda"},
    )
    provider = ITunesCandidateProvider(search)
    query = DiscoveryQuery(term="Koji Kondo - Gerudo Valley", source="seed", weight=1.0)

    candidates = provider.discover(_request(), [query])

    search.search_term.assert_called_once_with(
        "Koji Kondo - Gerudo Valley",
        wanted_artist="Koji Kondo",
        wanted_title="Gerudo Valley",
        limit=10,
    )
    assert candidates[0].genre == "Soundtrack"


def test_candidate_pool_deduplicates_and_merges_metadata():
    request = _request()
    low = CandidateTrack(TrackRef("A", "Same"), score=10, genre="")
    high = CandidateTrack(TrackRef("A", "Same"), score=80, genre="OST")

    pool = CandidatePool(request=request, candidates=(low, high)).deduplicated()

    assert pool.size == 1
    assert pool.candidates[0].score == 80
    assert pool.candidates[0].genre == "OST"


def test_merge_candidate_lists_prefers_seed_entries():
    seed = CandidateTrack(TrackRef("Koji Kondo", "Gerudo Valley"), score=100, source="seed", reasons=("seed",))
    discovered = CandidateTrack(TrackRef("Koji Kondo", "Gerudo Valley"), score=40, source="itunes")

    merged = merge_candidate_lists([discovered], [seed])

    assert len(merged) == 1
    assert merged[0].source == "seed"


def test_discovery_pipeline_collects_provider_candidates():
    provider = StaticCandidateProvider([
        CandidateTrack(TrackRef("Koji Kondo", "Lost Woods"), score=80, genre="OST"),
    ])

    result = DiscoveryPipeline([provider]).discover(_request())

    assert result.candidate_count == 1
    assert result.provider_stats == {"static": 1}
    assert result.deduplicated_count == 1


def test_generation_session_engine_preserves_seed_track():
    provider = StaticCandidateProvider([
        CandidateTrack(TrackRef("Someone Else", "Other Song"), score=95, genre="OST", mood="adventure"),
        CandidateTrack(TrackRef("Koji Kondo", "Dragon Roost Island"), score=70, genre="OST", mood="adventure"),
    ])
    engine = GenerationSessionEngine(DiscoveryPipeline([provider]))

    session = engine.generate(_request())

    assert session.generated_playlist.tracks[0] == TrackRef("Koji Kondo", "Gerudo Valley")
    assert "Rapport du labo musical" in session.report


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
        TrackRef("Koji Kondo", "Gerudo Valley"),
        TrackRef("Koji Kondo", "Lost Woods"),
    ]
