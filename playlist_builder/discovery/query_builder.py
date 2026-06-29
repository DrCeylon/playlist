from __future__ import annotations

from playlist_builder.discovery.models import DiscoveryQuery
from playlist_builder.planning.models import ConstraintKind, PlaylistRequest

MAX_DISCOVERY_QUERIES = 12


def build_discovery_queries(request: PlaylistRequest) -> list[DiscoveryQuery]:
    """Translate PlaylistRequest into catalog/search queries."""

    request.validate()
    queries: list[DiscoveryQuery] = []

    for seed in request.seeds:
        queries.append(DiscoveryQuery(term=seed.track.label, source="seed", weight=seed.weight))
        queries.append(DiscoveryQuery(term=seed.track.artist, source="seed_artist", weight=seed.weight * 0.6))

    for term in request.constraints.preferred_terms:
        queries.append(DiscoveryQuery(term=term, source="preferred_term", weight=0.7))

    for inclusion in request.constraints.inclusions:
        if inclusion.kind in (
            ConstraintKind.ARTIST,
            ConstraintKind.ALBUM,
            ConstraintKind.GENRE,
            ConstraintKind.MOOD,
            ConstraintKind.LANGUAGE,
            ConstraintKind.TERM,
        ):
            queries.append(
                DiscoveryQuery(
                    term=inclusion.value,
                    source=f"inclusion:{inclusion.kind.value}",
                    weight=inclusion.weight,
                )
            )

    deduped = _dedupe_queries(queries)
    return _limit_queries(deduped)


def _dedupe_queries(queries: list[DiscoveryQuery]) -> list[DiscoveryQuery]:
    by_term: dict[str, DiscoveryQuery] = {}
    for query in queries:
        term = query.term.strip().lower()
        if not term:
            continue
        existing = by_term.get(term)
        if existing is None or query.weight > existing.weight:
            by_term[term] = query
    return list(by_term.values())


def _limit_queries(queries: list[DiscoveryQuery]) -> list[DiscoveryQuery]:
    if len(queries) <= MAX_DISCOVERY_QUERIES:
        return queries
    return sorted(queries, key=lambda query: query.weight, reverse=True)[:MAX_DISCOVERY_QUERIES]
