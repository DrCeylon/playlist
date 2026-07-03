from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from playlist_builder.scoring.constants import (
    CATALOG_ARTIST_EXACT_WEIGHT,
    CATALOG_ARTIST_PARTIAL_WEIGHT,
    CATALOG_TITLE_EXACT_WEIGHT,
    CATALOG_TITLE_PARTIAL_WEIGHT,
    FUZZY_ARTIST_SIMILARITY_WEIGHT,
    FUZZY_ARTIST_TOKEN_WEIGHT,
    FUZZY_TITLE_SIMILARITY_WEIGHT,
    FUZZY_TITLE_TOKEN_WEIGHT,
    MIN_MATCH_SCORE,
)
from playlist_builder.scoring.models import MatchScore, ScoredMatch
from playlist_builder.scoring.normalization import extract_catalog_artist_title, normalize_text, token_set


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


def score_text_match(wanted_artist: str, wanted_title: str, candidate_artist: str, candidate_title: str) -> int:
    wanted_artist_norm = normalize_text(wanted_artist)
    wanted_title_norm = normalize_text(wanted_title)
    artist_norm = normalize_text(candidate_artist)
    title_norm = normalize_text(candidate_title)

    value = 0
    if wanted_artist_norm == artist_norm:
        value += CATALOG_ARTIST_EXACT_WEIGHT
    elif wanted_artist_norm in artist_norm or artist_norm in wanted_artist_norm:
        value += CATALOG_ARTIST_PARTIAL_WEIGHT

    if wanted_title_norm == title_norm:
        value += CATALOG_TITLE_EXACT_WEIGHT
    elif wanted_title_norm in title_norm or title_norm in wanted_title_norm:
        value += CATALOG_TITLE_PARTIAL_WEIGHT

    return value


def artist_name_matches(wanted_artist: str, candidate_artist: str) -> bool:
    wanted_artist_norm = normalize_text(wanted_artist)
    artist_norm = normalize_text(candidate_artist)
    if not wanted_artist_norm:
        return True
    if not artist_norm:
        return False
    if wanted_artist_norm == artist_norm:
        return True
    return wanted_artist_norm in artist_norm or artist_norm in wanted_artist_norm


def score_fuzzy_match(wanted_artist: str, wanted_title: str, candidate_artist: str, candidate_title: str) -> int:
    title_similarity = similarity_ratio(wanted_title, candidate_title)
    title_tokens = token_overlap(wanted_title, candidate_title)
    artist_similarity = similarity_ratio(wanted_artist, candidate_artist)
    artist_tokens = token_overlap(wanted_artist, candidate_artist)

    score = (
        title_similarity * FUZZY_TITLE_SIMILARITY_WEIGHT
        + title_tokens * FUZZY_TITLE_TOKEN_WEIGHT
        + artist_similarity * FUZZY_ARTIST_SIMILARITY_WEIGHT
        + artist_tokens * FUZZY_ARTIST_TOKEN_WEIGHT
    )
    return round(score)


class MatchScoringEngine:
    """Provider-agnostic track matching engine for catalog and resolution flows."""

    def score_catalog_item(self, wanted_artist: str, wanted_title: str, item: dict[str, Any]) -> int:
        artist, title = extract_catalog_artist_title(item)
        return score_text_match(wanted_artist, wanted_title, artist, title)

    def score_fuzzy_match(
        self,
        wanted_artist: str,
        wanted_title: str,
        candidate_artist: str,
        candidate_title: str,
    ) -> int:
        return score_fuzzy_match(wanted_artist, wanted_title, candidate_artist, candidate_title)

    def pick_best_catalog_match(
        self,
        wanted_artist: str,
        wanted_title: str,
        results: list[dict[str, Any]],
        *,
        min_score: int = MIN_MATCH_SCORE,
    ) -> dict[str, Any] | None:
        if not results:
            return None

        best_score = -1
        best: dict[str, Any] | None = None
        for item in results:
            score = self.score_catalog_item(wanted_artist, wanted_title, item)
            if score > best_score:
                best_score = score
                best = item

        if best is None or best_score < min_score:
            return None
        return best

    def rank_fuzzy_matches(
        self,
        wanted_artist: str,
        wanted_title: str,
        candidates: list[tuple[str, str]],
    ) -> list[ScoredMatch]:
        ranked = [
            ScoredMatch(
                artist=artist,
                title=title,
                score=MatchScore(self.score_fuzzy_match(wanted_artist, wanted_title, artist, title)),
            )
            for artist, title in candidates
        ]
        return sorted(ranked, key=lambda match: match.score.value, reverse=True)


def score_track_match(wanted_artist: str, wanted_title: str, item: dict[str, Any]) -> int:
    return MatchScoringEngine().score_catalog_item(wanted_artist, wanted_title, item)


def pick_best_match(
    wanted_artist: str,
    wanted_title: str,
    results: list[dict[str, Any]],
    *,
    min_score: int = MIN_MATCH_SCORE,
) -> dict[str, Any] | None:
    return MatchScoringEngine().pick_best_catalog_match(
        wanted_artist,
        wanted_title,
        results,
        min_score=min_score,
    )
