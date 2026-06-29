from __future__ import annotations

from playlist_builder.discovery.models import DiscoveryQuery


def wanted_match_fields(query: DiscoveryQuery) -> tuple[str, str]:
    term = query.term.strip()
    if query.source == "seed" and " - " in term:
        artist, title = term.split(" - ", 1)
        return artist.strip(), title.strip()
    if query.source == "seed_artist":
        return term, ""
    return "", term
