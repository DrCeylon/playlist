from __future__ import annotations

import re
import unicodedata

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "de",
    "du",
    "feat",
    "featuring",
    "in",
    "la",
    "le",
    "les",
    "of",
    "the",
    "with",
    "ft",
    "vs",
}

_MOOD_KEYWORDS = {
    "calm": ("calm", "chill", "relax", "soft"),
    "dramatic": ("dramatic", "epic", "orchestral"),
    "energetic": ("energy", "energetic", "intense", "power"),
    "happy": ("happy", "joy", "sunshine", "smile"),
    "melancholic": ("sad", "lonely", "tears", "blue"),
    "romantic": ("love", "heart", "kiss", "romance"),
    "summer": ("summer", "sun", "beach", "festival"),
    "upbeat": ("upbeat", "party", "dance", "groove"),
}

_GENRE_HINTS = {
    "alternative": ("alternative", "alt rock", "indie"),
    "dance": ("dance", "edm", "house", "club"),
    "electronic": ("electronic", "electro", "synth"),
    "hip-hop": ("hip hop", "rap", "trap"),
    "pop": ("pop",),
    "rock": ("rock", "metal", "punk"),
}


def suggest_keywords(
    *,
    artist_name: str = "",
    artist_type: str = "",
    track_title: str = "",
    album_title: str = "",
    release_year: int | None = None,
    primary_genre_name: str = "",
) -> list[str]:
    """Suggest playlist keywords from autocomplete metadata without provider coupling."""
    suggestions: list[str] = []

    def add(value: str) -> None:
        normalized = _normalize_keyword(value)
        if not normalized or normalized in suggestions:
            return
        suggestions.append(normalized)

    if primary_genre_name.strip():
        add(primary_genre_name)

    for keyword in _genre_hints_from_text(primary_genre_name):
        add(keyword)

    for keyword in _title_keywords(track_title):
        add(keyword)

    if album_title.strip():
        for keyword in _title_keywords(album_title, max_tokens=2):
            add(keyword)

    if release_year is not None and release_year >= 1900:
        decade = (release_year // 10) * 10
        add(f"{decade}s")

    for mood, triggers in _MOOD_KEYWORDS.items():
        haystack = f"{track_title} {album_title}".casefold()
        if any(trigger in haystack for trigger in triggers):
            add(mood)

    if artist_type.strip().casefold() in {"band", "group", "orchestra"}:
        add(artist_type.strip().casefold())

    # Artist name is a weak signal; only use it when nothing else was inferred.
    if not suggestions and artist_name.strip():
        for keyword in _title_keywords(artist_name, max_tokens=1):
            add(keyword)

    return suggestions[:8]


def _genre_hints_from_text(value: str) -> list[str]:
    lowered = value.casefold()
    hints: list[str] = []
    for keyword, triggers in _GENRE_HINTS.items():
        if any(trigger in lowered for trigger in triggers):
            hints.append(keyword)
    return hints


def _title_keywords(value: str, *, max_tokens: int = 3) -> list[str]:
    cleaned = re.sub(r"\([^)]*\)", " ", value)
    cleaned = re.sub(r"\[[^]]*\]", " ", cleaned)
    cleaned = re.sub(r"(?i)\bfeat\.?.*$", " ", cleaned)
    tokens = [_normalize_keyword(token) for token in re.split(r"[^a-zA-Z0-9]+", cleaned)]
    result: list[str] = []
    for token in tokens:
        if not token or token in _STOP_WORDS or len(token) < 3:
            continue
        if token not in result:
            result.append(token)
        if len(result) >= max_tokens:
            break
    return result


def _normalize_keyword(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    return normalized
