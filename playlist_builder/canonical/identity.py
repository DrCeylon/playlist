from __future__ import annotations

import re
import unicodedata

_IDENTITY_SEPARATOR = "::"
_NON_WORD_PATTERN = re.compile(r"[^a-z0-9]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_identity_component(value: str) -> str:
    """Normalize a single identity component for stable cross-provider keys."""

    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower().replace("&", " and ")
    text = _NON_WORD_PATTERN.sub(" ", text)
    return _WHITESPACE_PATTERN.sub(" ", text).strip()


def track_identity_key(artist: str, title: str, *, isrc: str | None = None) -> str:
    """Build a provider-neutral identity key for caching and deduplication.

    ISRC takes precedence when available because it is globally unique.
    """

    if isrc and isrc.strip():
        return f"isrc{_IDENTITY_SEPARATOR}{isrc.strip().lower()}"

    artist_norm = normalize_identity_component(artist)
    title_norm = normalize_identity_component(title)
    return f"{artist_norm}{_IDENTITY_SEPARATOR}{title_norm}"
