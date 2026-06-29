from __future__ import annotations

from playlist_builder.core.models import TrackRef
from playlist_builder.resolver.constants import MIN_ACCEPTABLE_SCORE
from playlist_builder.resolver.models import ResolverCandidate, ResolverDecision
from playlist_builder.resolver.scoring import score_candidate


def rank_candidates(wanted: TrackRef, candidates: list[ResolverCandidate]) -> list[ResolverCandidate]:
    ranked = [
        ResolverCandidate(
            wanted=wanted,
            artist=candidate.artist,
            title=candidate.title,
            persistent_id=candidate.persistent_id,
            query=candidate.query,
            score=score_candidate(wanted, candidate.artist, candidate.title),
        )
        for candidate in candidates
    ]
    return sorted(ranked, key=lambda candidate: candidate.score, reverse=True)


def select_best_candidate(wanted: TrackRef, candidates: list[ResolverCandidate]) -> ResolverDecision:
    ranked = rank_candidates(wanted, _dedupe(candidates))
    selected = ranked[0] if ranked and ranked[0].score >= MIN_ACCEPTABLE_SCORE else None
    return ResolverDecision(wanted=wanted, selected=selected, candidates=tuple(ranked))


def _dedupe(candidates: list[ResolverCandidate]) -> list[ResolverCandidate]:
    by_key: dict[tuple[str, str], ResolverCandidate] = {}
    for candidate in candidates:
        key = (candidate.artist.strip().lower(), candidate.title.strip().lower())
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = candidate
    return list(by_key.values())
