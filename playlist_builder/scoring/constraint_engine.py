from __future__ import annotations

from playlist_builder.planning.models import CandidateTrack, ConstraintKind, GenerationConstraints
from playlist_builder.scoring.constants import EXCLUSION_PENALTY, INCLUSION_BOOST, PREFERRED_TERM_BOOST


def apply_text_preferences(candidate: CandidateTrack, constraints: GenerationConstraints) -> CandidateTrack:
    text = candidate.searchable_text
    score = candidate.score
    reasons = list(candidate.reasons)

    if candidate.explicit and not constraints.allow_explicit:
        score += EXCLUSION_PENALTY
        reasons.append("excluded:explicit")

    for term in constraints.preferred_terms:
        if term.lower() in text:
            score += PREFERRED_TERM_BOOST
            reasons.append(f"preferred:{term}")

    for term in constraints.excluded_terms:
        if term.lower() in text:
            score += EXCLUSION_PENALTY
            reasons.append(f"excluded:{term}")

    for inclusion in constraints.inclusions:
        if _rule_matches(candidate, inclusion.kind, inclusion.value):
            boost = INCLUSION_BOOST * inclusion.weight
            score += boost
            reasons.append(f"included:{inclusion.kind.value}:{inclusion.value}")

    for exclusion in constraints.exclusions:
        if _rule_matches(candidate, exclusion.kind, exclusion.value):
            score += EXCLUSION_PENALTY
            reasons.append(f"excluded:{exclusion.kind.value}:{exclusion.value}")

    return CandidateTrack(
        track=candidate.track,
        score=score,
        source=candidate.source,
        reasons=tuple(reasons),
        album=candidate.album,
        genre=candidate.genre,
        mood=candidate.mood,
        language=candidate.language,
        energy=candidate.energy,
        explicit=candidate.explicit,
    )


def rank_candidates(candidates: list[CandidateTrack], constraints: GenerationConstraints) -> list[CandidateTrack]:
    adjusted = [apply_text_preferences(candidate, constraints) for candidate in candidates]
    return sorted(adjusted, key=lambda candidate: candidate.score, reverse=True)


def is_rejected(candidate: CandidateTrack) -> bool:
    return candidate.score <= EXCLUSION_PENALTY / 2 or any(
        reason.startswith("excluded:") for reason in candidate.reasons
    )


def _rule_matches(candidate: CandidateTrack, kind: ConstraintKind, value: str) -> bool:
    expected = value.strip().lower()
    if not expected:
        return False

    if kind == ConstraintKind.ARTIST:
        return expected in candidate.track.artist.lower()
    if kind == ConstraintKind.TRACK:
        return expected in candidate.track.title.lower()
    if kind == ConstraintKind.ALBUM:
        return expected in candidate.album.lower()
    if kind == ConstraintKind.GENRE:
        return expected in candidate.genre.lower()
    if kind == ConstraintKind.MOOD:
        return expected in candidate.mood.lower()
    if kind == ConstraintKind.LANGUAGE:
        return expected in candidate.language.lower()
    return expected in candidate.searchable_text
