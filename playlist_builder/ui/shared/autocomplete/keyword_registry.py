from __future__ import annotations

import re
import unicodedata

from playlist_builder.ui.shared.dto.autocomplete import KeywordSuggestion

_CURATED_KEYWORDS: tuple[str, ...] = (
    "Summer",
    "Pool Party",
    "Relax",
    "Driving",
    "Workout",
    "Focus",
    "Chill",
    "Party",
    "Sunset",
    "Night",
    "Morning",
    "Rain",
    "Road Trip",
    "Dance",
    "Romantic",
    "Energy",
    "Calm",
    "Happy",
    "Melancholic",
    "Festival",
    "Beach",
    "Winter",
    "Spring",
    "Autumn",
)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


def _keyword_id(label: str) -> str:
    slug = _normalize(label)
    return slug or "keyword"


def search_keywords(query: str, *, limit: int = 10) -> tuple[KeywordSuggestion, ...]:
    normalized_query = query.strip().casefold()
    suggestions: list[KeywordSuggestion] = []
    seen: set[str] = set()

    for label in _CURATED_KEYWORDS:
        keyword_id = _keyword_id(label)
        if keyword_id in seen:
            continue
        if not normalized_query or normalized_query in label.casefold():
            suggestions.append(KeywordSuggestion(id=keyword_id, label=label))
            seen.add(keyword_id)
        if len(suggestions) >= limit:
            return tuple(suggestions)

    if normalized_query and len(suggestions) < limit:
        custom = query.strip()
        if custom:
            keyword_id = _keyword_id(custom)
            if keyword_id not in seen:
                suggestions.append(KeywordSuggestion(id=keyword_id, label=custom))
    return tuple(suggestions[:limit])
