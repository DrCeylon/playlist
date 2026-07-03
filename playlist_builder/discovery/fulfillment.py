from __future__ import annotations

from playlist_builder.discovery.models import DiscoveryQuery
from playlist_builder.planning.models import CandidateTrack, PlaylistRequest
from playlist_builder.planning.planner import PlaylistPlanner

MAX_DISCOVERY_QUERIES_BASE = 12
MAX_DISCOVERY_QUERIES_CAP = 48


def max_discovery_queries_for(request: PlaylistRequest) -> int:
    target = PlaylistPlanner._target_count(request)
    return min(MAX_DISCOVERY_QUERIES_CAP, max(MAX_DISCOVERY_QUERIES_BASE, target * 2))


def build_expansion_queries(request: PlaylistRequest, *, pass_index: int) -> list[DiscoveryQuery]:
    """Generate broader catalog queries when the first discovery pass under-delivers."""

    request.validate()
    queries: list[DiscoveryQuery] = []
    weight = max(0.35, 0.7 - pass_index * 0.15)

    for seed in request.seeds:
        artist = seed.track.artist.strip()
        title = seed.track.title.strip()
        if pass_index == 0:
            if artist:
                queries.append(DiscoveryQuery(term=artist, source="expansion:artist", weight=weight))
            if title:
                queries.append(DiscoveryQuery(term=title, source="expansion:title", weight=weight * 0.9))
        elif pass_index == 1:
            if artist and title:
                queries.append(
                    DiscoveryQuery(
                        term=f"{artist} {title}",
                        source="expansion:artist_title",
                        weight=weight,
                    )
                )
            for token in title.split():
                token = token.strip()
                if len(token) >= 4:
                    queries.append(
                        DiscoveryQuery(term=token, source="expansion:title_token", weight=weight * 0.75)
                    )
        else:
            if artist:
                queries.append(
                    DiscoveryQuery(term=f"{artist} similar", source="expansion:related", weight=weight * 0.6)
                )
            for term in request.constraints.preferred_terms:
                queries.append(
                    DiscoveryQuery(term=term, source="expansion:preferred", weight=weight * 0.65)
                )

    deduped: dict[str, DiscoveryQuery] = {}
    for query in queries:
        term = query.term.strip().lower()
        if not term:
            continue
        existing = deduped.get(term)
        if existing is None or query.weight > existing.weight:
            deduped[term] = query
    return list(deduped.values())


def explain_shortfall(
    request: PlaylistRequest,
    *,
    target: int,
    selected: int,
    discovered: int,
    eligible: int,
    rejected: int,
    passes_used: int,
) -> str:
    if selected >= target:
        return ""

    parts = [
        f"Demandé : {target} morceau(x). Obtenu : {selected}.",
    ]
    if discovered < target:
        parts.append(
            f"Seulement {discovered} candidat(s) unique(s) trouvé(s) dans le catalogue "
            f"après {passes_used} passe(s) de recherche."
        )
    if rejected:
        parts.append(f"{rejected} candidat(s) écarté(s) par les exclusions ou filtres qualité.")
    if eligible < target and discovered >= target:
        parts.append(
            "Assez de candidats découverts, mais trop peu ne passent les contraintes actuelles."
        )
    parts.append(
        "Essayez d'élargir les mots-clés, de réduire les exclusions, "
        "ou d'ajouter un second morceau d'inspiration."
    )
    return " ".join(parts)
