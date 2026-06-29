from __future__ import annotations

from playlist_builder.planning.models import CandidateTrack, GenerationConstraints


def apply_text_preferences(candidate: CandidateTrack, constraints: GenerationConstraints) -> CandidateTrack:
    """Apply simple deterministic boosts/penalties.

    This is intentionally lightweight for Phase 2. It gives the future UI and
    generator a stable scoring contract without requiring MusicKit yet.
    """

    text = f"{candidate.track.artist} {candidate.track.title}".lower()
    score = candidate.score
    reasons = list(candidate.reasons)

    for term in constraints.preferred_terms:
        if term.lower() in text:
            score += 10
            reasons.append(f"preferred:{term}")

    for term in constraints.excluded_terms:
        if term.lower() in text:
            score -= 100
            reasons.append(f"excluded:{term}")

    return CandidateTrack(
        track=candidate.track,
        score=score,
        source=candidate.source,
        reasons=tuple(reasons),
    )


def rank_candidates(candidates: list[CandidateTrack], constraints: GenerationConstraints) -> list[CandidateTrack]:
    adjusted = [apply_text_preferences(candidate, constraints) for candidate in candidates]
    return sorted(adjusted, key=lambda candidate: candidate.score, reverse=True)
