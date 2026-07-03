from __future__ import annotations

import re
import unicodedata

from playlist_builder.ui.shared.dto.autocomplete import GenreSuggestion

_GENRE_ENTRIES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("alternative-rock", "Alternative Rock", ("Rock alternatif", "Alt Rock")),
    ("hip-hop", "Hip-Hop", ("Hip Hop", "Hiphop", "Rap")),
    ("heavy-metal", "Heavy Metal", ("Metal", "Metal lourd")),
    ("electronic", "Electronic", ("Électronique", "Electro", "EDM")),
    ("pop", "Pop", ()),
    ("rock", "Rock", ()),
    ("jazz", "Jazz", ()),
    ("classical", "Classical", ("Classique", "Classical Music")),
    ("r-and-b", "R&B", ("RnB", "R and B", "Rhythm and Blues")),
    ("soul", "Soul", ()),
    ("funk", "Funk", ()),
    ("country", "Country", ("Country Music",)),
    ("blues", "Blues", ()),
    ("reggae", "Reggae", ()),
    ("latin", "Latin", ("Latino",)),
    ("k-pop", "K-Pop", ("Kpop", "K Pop")),
    ("indie", "Indie", ("Indie Rock", "Indie Pop")),
    ("ambient", "Ambient", ()),
    ("house", "House", ("Deep House",)),
    ("techno", "Techno", ()),
    ("trance", "Trance", ()),
    ("dubstep", "Dubstep", ()),
    ("folk", "Folk", ("Folk Rock",)),
    ("punk", "Punk", ("Punk Rock",)),
    ("soundtrack", "Soundtrack", ("Bande originale", "Film Score")),
)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def _build_index() -> tuple[GenreSuggestion, ...]:
    entries: list[GenreSuggestion] = []
    for genre_id, display_name, synonyms in _GENRE_ENTRIES:
        entries.append(GenreSuggestion(id=genre_id, display_name=display_name, synonyms=synonyms))
    return tuple(entries)


CANONICAL_GENRES: tuple[GenreSuggestion, ...] = _build_index()


def search_genres(query: str, *, limit: int = 10) -> tuple[GenreSuggestion, ...]:
    normalized_query = _normalize(query)
    if not normalized_query:
        return CANONICAL_GENRES[:limit]

    scored: list[tuple[int, GenreSuggestion]] = []
    for genre in CANONICAL_GENRES:
        candidates = (genre.display_name, *genre.synonyms)
        best = 0
        for candidate in candidates:
            normalized_candidate = _normalize(candidate)
            if normalized_candidate == normalized_query:
                best = max(best, 100)
            elif normalized_candidate.startswith(normalized_query):
                best = max(best, 80)
            elif normalized_query in normalized_candidate:
                best = max(best, 60)
        if best:
            scored.append((best, genre))

    scored.sort(key=lambda item: (-item[0], item[1].display_name.casefold()))
    return tuple(item[1] for item in scored[:limit])
