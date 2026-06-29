from __future__ import annotations

from difflib import SequenceMatcher

from playlist_builder.core.models import TrackRef
from playlist_builder.resolver.constants import MIN_ACCEPTABLE_SCORE
from playlist_builder.resolver.normalization import normalize_text, token_set


def similarity_ratio(left: str, right: str) -> float:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return 0.0
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def token_overlap(left: str, right: str) -> float:
    left_tokens = token_set(left)
    right_tokens = token_set(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def score_candidate(wanted: TrackRef, candidate_artist: str, candidate_title: str) -> int:
    """Score a candidate on a 0-100 scale."""

    title_similarity = similarity_ratio(wanted.title, candidate_title)
    title_tokens = token_overlap(wanted.title, candidate_title)
    artist_similarity = similarity_ratio(wanted.artist, candidate_artist)
    artist_tokens = token_overlap(wanted.artist, candidate_artist)

    score = (
        title_similarity * 45
        + title_tokens * 25
        + artist_similarity * 20
        + artist_tokens * 10
    )
    return round(score)


def is_acceptable_match(wanted: TrackRef, candidate_artist: str, candidate_title: str) -> bool:
    """Python-side guardrail for future multi-candidate resolution."""

    return score_candidate(wanted, candidate_artist, candidate_title) >= MIN_ACCEPTABLE_SCORE
