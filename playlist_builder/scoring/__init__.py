"""Unified scoring engine for catalog matching, fuzzy resolution, and planning constraints."""

from playlist_builder.scoring.constants import (
    EXCLUSION_PENALTY,
    INCLUSION_BOOST,
    MIN_ACCEPTABLE_SCORE,
    MIN_MATCH_SCORE,
    MIN_MUSICKIT_MATCH_SCORE,
)
from playlist_builder.scoring.constraint_engine import (
    apply_text_preferences,
    is_rejected,
    rank_candidates,
)
from playlist_builder.scoring.match_engine import (
    MatchScoringEngine,
    pick_best_match,
    score_track_match,
    similarity_ratio,
    token_overlap,
)
from playlist_builder.scoring.models import MatchScore, ScoredMatch
from playlist_builder.scoring.normalization import normalize_text, token_set
from playlist_builder.scoring.resolution import (
    is_acceptable_match,
    rank_resolution_candidates,
    score_resolution_match,
    select_best_resolution,
)

__all__ = [
    "EXCLUSION_PENALTY",
    "INCLUSION_BOOST",
    "MIN_ACCEPTABLE_SCORE",
    "MIN_MATCH_SCORE",
    "MIN_MUSICKIT_MATCH_SCORE",
    "MatchScore",
    "MatchScoringEngine",
    "ScoredMatch",
    "apply_text_preferences",
    "is_acceptable_match",
    "is_rejected",
    "normalize_text",
    "pick_best_match",
    "rank_candidates",
    "rank_resolution_candidates",
    "score_resolution_match",
    "score_track_match",
    "select_best_resolution",
    "similarity_ratio",
    "token_set",
    "token_overlap",
]
