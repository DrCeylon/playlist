from __future__ import annotations

from playlist_builder.discovery.models import DiscoveryQuery
from playlist_builder.planning.models import ConstraintKind, PlaylistRequest


def build_discovery_queries(request: PlaylistRequest) -> list[DiscoveryQuery]:
    """Translate PlaylistRequest into catalog/search queries.

    This first implementation is intentionally deterministic and explainable.
    Later, a UI can show exactly which queries were produced from the request.
    """

    request.validate()
    queries: list[DiscoveryQuery] = []

    for seed in request.seeds:
        queries.append(DiscoveryQuery(term=seed.track.label, source="seed", weight=seed.weight))
        queries.append(DiscoveryQuery(term=seed.track.artist, source="seed_artist", weight=seed.weight * 0.6))

    for term in request.constraints.preferred_terms:
        queries.append(DiscoveryQuery(term=term, source="preferred_term", weight=0.7))

    for inclusion in request.constraints.inclusions:
        if inclusion.kind in (ConstraintKind.ARTIST, ConstraintKind.ALBUM, ConstraintKind.GENRE, ConstraintKind.MOOD, ConstraintKind.LANGUAGE, ConstraintKind.TERM):
            queries.append(
                DiscoveryQuery(
                    term=inclusion.value,
                    source=f"inclusion:{inclusion.kind.value}",
                    weight=inclusion.weight,
                )
            )

    return _dedupe_queries(queries)


def _dedupe_queries(queries: list[DiscoveryQuery]) -> list[DiscoveryQuery]:
    by_key: dict[tuple[str, str], DiscoveryQuery] = {}
    for query in queries:
        key = (query.term.strip().lower(), query.source)
        if not key[0]:
            continue
        existing = by_key.get(key)
        if existing is None or query.weight > existing.weight:
            by_key[key] = query
    return list(by_key.values())
