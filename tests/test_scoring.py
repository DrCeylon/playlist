from __future__ import annotations

import pytest

from playlist_builder.catalog import scoring as catalog_scoring
from playlist_builder.core.models import TrackRef
from playlist_builder.planning import scoring as planning_scoring
from playlist_builder.planning.models import (
    CandidateTrack,
    ConstraintKind,
    ExclusionRule,
    GenerationConstraints,
    InclusionRule,
)
from playlist_builder.resolver import normalization as resolver_normalization
from playlist_builder.resolver import scoring as resolver_scoring
from playlist_builder.scoring import (
    MatchScoringEngine,
    apply_text_preferences,
    is_acceptable_match,
    is_rejected,
    normalize_text,
    pick_best_match,
    rank_resolution_candidates,
    score_track_match,
    select_best_resolution,
    similarity_ratio,
    token_overlap,
)
from playlist_builder.scoring.constants import (
    MIN_ACCEPTABLE_SCORE,
    MIN_MATCH_SCORE,
    MIN_MUSICKIT_MATCH_SCORE,
)
from playlist_builder.scoring.resolution import ResolutionCandidate, score_resolution_match


def test_catalog_facade_delegates_to_match_engine():
    item = {"artistName": "Kygo", "trackName": "Firestone"}
    assert catalog_scoring.score_track_match("Kygo", "Firestone", item) == 100
    assert score_track_match("Kygo", "Firestone", item) == 100


def test_catalog_facade_exports_threshold_constants():
    assert catalog_scoring.MIN_MATCH_SCORE == MIN_MATCH_SCORE
    assert catalog_scoring.MIN_MUSICKIT_MATCH_SCORE == MIN_MUSICKIT_MATCH_SCORE


def test_pick_best_match_rejects_low_confidence_results():
    results = [{"artistName": "Unknown Artist", "trackName": "Random Song"}]
    assert pick_best_match("Kygo", "Firestone", results) is None


def test_resolver_facade_delegates_fuzzy_scoring():
    wanted = TrackRef("Koji Kondo", "Gerudo Valley")
    good = resolver_scoring.score_candidate(wanted, "Nintendo Sound Team", "Gerudo Valley")
    bad = resolver_scoring.score_candidate(wanted, "Mariah Carey", "Fantasy")
    assert good > bad
    assert good == score_resolution_match(wanted, "Nintendo Sound Team", "Gerudo Valley")


def test_resolver_facade_exports_similarity_helpers():
    assert resolver_normalization.normalize_text("Gérudo Valley (Live)") == normalize_text("Gérudo Valley (Live)")
    assert token_overlap("Super Mario Bros Main Theme", "Super Mario Main Theme") > 0.5
    assert similarity_ratio("Gerudo Valley", "Gerudo Valley OST") > similarity_ratio("Gerudo Valley", "Fantasy")


def test_is_acceptable_match_uses_shared_threshold():
    wanted = TrackRef("Koji Kondo", "Gerudo Valley")
    assert is_acceptable_match(wanted, "Nintendo Sound Team", "Gerudo Valley")
    assert resolver_scoring.is_acceptable_match(wanted, "Nintendo Sound Team", "Gerudo Valley")
    assert not is_acceptable_match(wanted, "Mariah Carey", "Fantasy")


def test_planning_facade_applies_structured_exclusion():
    candidate = CandidateTrack(
        TrackRef("Pitbull", "Give Me Everything"),
        score=80,
        genre="Dance",
    )
    constraints = GenerationConstraints(
        target_track_count=1,
        exclusions=(ExclusionRule(ConstraintKind.ARTIST, "Pitbull"),),
    )
    adjusted = planning_scoring.apply_text_preferences(candidate, constraints)
    assert planning_scoring.is_rejected(adjusted)
    assert is_rejected(adjusted)


def test_planning_facade_applies_structured_inclusion():
    candidate = CandidateTrack(
        TrackRef("Artist B", "Track B"),
        score=20,
        mood="adventure",
    )
    constraints = GenerationConstraints(
        target_track_count=1,
        inclusions=(InclusionRule(ConstraintKind.MOOD, "adventure", weight=2),),
    )
    adjusted = planning_scoring.apply_text_preferences(candidate, constraints)
    assert adjusted.score > candidate.score


def test_match_scoring_engine_ranks_fuzzy_matches():
    engine = MatchScoringEngine()
    ranked = engine.rank_fuzzy_matches(
        "Koji Kondo",
        "Gerudo Valley",
        [
            ("Mariah Carey", "Fantasy"),
            ("Nintendo Sound Team", "Gerudo Valley"),
        ],
    )
    assert ranked[0].artist == "Nintendo Sound Team"
    assert ranked[0].score.value >= MIN_ACCEPTABLE_SCORE


def test_rank_resolution_candidates_dedupes_and_sorts():
    wanted = TrackRef("Kygo", "Firestone")
    candidates = [
        ResolutionCandidate("Kygo", "Firestone"),
        ResolutionCandidate("Kygo", "Firestone"),
        ResolutionCandidate("Avicii", "Levels"),
    ]
    ranked = rank_resolution_candidates(wanted, candidates)
    assert len(ranked) == 2
    assert ranked[0].title == "Firestone"


def test_select_best_resolution_returns_none_for_weak_matches():
    wanted = TrackRef("Kygo", "Firestone")
    decision = select_best_resolution(
        wanted,
        [ResolutionCandidate("Unknown", "Other Song")],
    )
    assert decision.selected is None
    assert decision.wanted == wanted


def test_select_best_resolution_accepts_strong_match():
    wanted = TrackRef("Kygo", "Firestone")
    decision = select_best_resolution(
        wanted,
        [ResolutionCandidate("Kygo", "Firestone")],
    )
    assert decision.selected is not None
    assert decision.selected.score == 100
