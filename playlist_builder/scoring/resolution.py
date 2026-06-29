from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.core.models import TrackRef
from playlist_builder.scoring.constants import MIN_ACCEPTABLE_SCORE
from playlist_builder.scoring.match_engine import MatchScoringEngine, score_fuzzy_match


@dataclass(frozen=True, slots=True)
class ResolutionCandidate:
    artist: str
    title: str
    persistent_id: str = ""
    query: str = ""
    score: int = 0


@dataclass(frozen=True, slots=True)
class ResolutionDecision:
    wanted: TrackRef
    selected: ResolutionCandidate | None
    candidates: tuple[ResolutionCandidate, ...] = ()


def score_resolution_match(wanted: TrackRef, candidate_artist: str, candidate_title: str) -> int:
    return score_fuzzy_match(wanted.artist, wanted.title, candidate_artist, candidate_title)


def is_acceptable_match(wanted: TrackRef, candidate_artist: str, candidate_title: str) -> bool:
    return score_resolution_match(wanted, candidate_artist, candidate_title) >= MIN_ACCEPTABLE_SCORE


def rank_resolution_candidates(
    wanted: TrackRef,
    candidates: list[ResolutionCandidate],
) -> list[ResolutionCandidate]:
    engine = MatchScoringEngine()
    deduped = _dedupe_candidates(candidates)
    ranked = [
        ResolutionCandidate(
            artist=candidate.artist,
            title=candidate.title,
            persistent_id=candidate.persistent_id,
            query=candidate.query,
            score=engine.score_fuzzy_match(wanted.artist, wanted.title, candidate.artist, candidate.title),
        )
        for candidate in deduped
    ]
    return sorted(ranked, key=lambda candidate: candidate.score, reverse=True)


def select_best_resolution(wanted: TrackRef, candidates: list[ResolutionCandidate]) -> ResolutionDecision:
    ranked = rank_resolution_candidates(wanted, candidates)
    selected = ranked[0] if ranked and ranked[0].score >= MIN_ACCEPTABLE_SCORE else None
    return ResolutionDecision(wanted=wanted, selected=selected, candidates=tuple(ranked))


def _dedupe_candidates(candidates: list[ResolutionCandidate]) -> list[ResolutionCandidate]:
    seen: set[tuple[str, str]] = set()
    result: list[ResolutionCandidate] = []
    for candidate in candidates:
        identifier = (candidate.artist.strip().lower(), candidate.title.strip().lower())
        if identifier in seen:
            continue
        seen.add(identifier)
        result.append(candidate)
    return result
