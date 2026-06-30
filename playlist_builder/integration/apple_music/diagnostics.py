from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.scoring.resolution import ResolutionCandidate


@dataclass(frozen=True, slots=True)
class AppleMusicQueryTrace:
    query: str
    candidates: int


@dataclass(frozen=True, slots=True)
class AppleMusicResolutionTrace:
    cache_hit: bool = False
    catalog_acquired: bool = False
    queries: tuple[AppleMusicQueryTrace, ...] = ()
    candidates: tuple[ResolutionCandidate, ...] = ()
    accepted: ResolutionCandidate | None = None
    reason: str = ""

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def best_score(self) -> int:
        return self.candidates[0].score if self.candidates else 0

    def summary(self) -> str:
        if self.reason:
            return self.reason
        if self.cache_hit:
            return "Cache hit IdentityCache."
        if self.catalog_acquired:
            return "Résolu après acquisition depuis le catalogue iTunes."
        if not self.candidates:
            query_terms = ", ".join(trace.query for trace in self.queries if trace.query)
            suffix = f" Requêtes: {query_terms}" if query_terms else ""
            return f"Aucun candidat retourné par Music.app.{suffix}"
        best = self.candidates[0]
        return (
            "Aucun candidat acceptable dans la bibliothèque Apple Music. "
            f"Meilleur: {best.artist} - {best.title} "
            f"score={best.score}."
        )


def trace_from_candidates(
    *,
    candidates: tuple[ResolutionCandidate, ...],
    expected_queries: tuple[str, ...] = (),
    accepted: ResolutionCandidate | None = None,
    cache_hit: bool = False,
    catalog_acquired: bool = False,
    reason: str = "",
) -> AppleMusicResolutionTrace:
    query_counts: dict[str, int] = {query: 0 for query in expected_queries}
    for candidate in candidates:
        if candidate.query:
            query_counts[candidate.query] = query_counts.get(candidate.query, 0) + 1

    return AppleMusicResolutionTrace(
        cache_hit=cache_hit,
        catalog_acquired=catalog_acquired,
        queries=tuple(AppleMusicQueryTrace(query, count) for query, count in query_counts.items()),
        candidates=candidates,
        accepted=accepted,
        reason=reason,
    )
