from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.core.models import TrackRef
from playlist_builder.resolver.constants import MAX_QUERY_VARIANTS, _GENERIC_SECTIONS
from playlist_builder.resolver.normalization import normalize_text

_CONTEXT_ALIASES: tuple[tuple[tuple[str, ...], tuple[tuple[str, str, float], ...]], ...] = (
    (
        ("gerudo", "zelda"),
        (
            ("Zelda {title}", "alias_zelda_title", 0.72),
            ("Legend of Zelda {title}", "alias_legend_of_zelda_title", 0.70),
        ),
    ),
    (
        ("mario",),
        (("Nintendo {title}", "alias_nintendo_title", 0.70),),
    ),
)


@dataclass(frozen=True, slots=True)
class QueryVariant:
    term: str
    reason: str
    weight: float = 1.0


def generate_query_variants(track: TrackRef) -> list[QueryVariant]:
    """Generate ordered search variants from precise to broad.

    Apple Music.app search is library-scoped and inconsistent across local
    metadata. The provider gateway must therefore ask broadly, collect
    candidates, and let Python scoring decide. Query variants are still capped to
    avoid excessive AppleScript calls.
    """

    title = track.title.strip()
    artist = track.artist.strip()
    section = track.section.strip()
    normalized_title = normalize_text(title)
    normalized_artist = normalize_text(artist)

    raw_variants = [
        QueryVariant(f"{title} {artist}", "title_artist", 1.0),
        QueryVariant(f"{artist} {title}", "artist_title", 0.98),
        QueryVariant(title, "title", 0.90),
    ]

    raw_variants.extend(_title_keyword_variants(title, normalized_title))

    if artist:
        raw_variants.append(QueryVariant(artist, "artist", 0.72))
        raw_variants.extend(_artist_keyword_variants(artist, normalized_artist))

    for tokens, aliases in _CONTEXT_ALIASES:
        if any(token in normalized_title for token in tokens):
            for term_template, reason, weight in aliases:
                raw_variants.append(QueryVariant(term_template.format(title=title), reason, weight))

    if section and normalize_text(section) not in _GENERIC_SECTIONS:
        raw_variants.extend(
            [
                QueryVariant(f"{section} {title}", "section_title", 0.70),
                QueryVariant(f"{title} {section}", "title_section", 0.68),
            ]
        )

    return _dedupe(raw_variants)[:MAX_QUERY_VARIANTS]


def _title_keyword_variants(title: str, normalized_title: str) -> list[QueryVariant]:
    tokens = normalized_title.split()
    if len(tokens) <= 1:
        return []

    variants: list[QueryVariant] = []
    # The first meaningful token is often enough for Music.app to return useful
    # library candidates (e.g. "Firestone", "Fantasy", "Sunny").
    variants.append(QueryVariant(tokens[0], "title_first_token", 0.62))

    # Two-token windows help with long classical / soundtrack titles.
    if len(tokens) >= 2:
        variants.append(QueryVariant(" ".join(tokens[:2]), "title_first_two_tokens", 0.66))
    if len(tokens) >= 3:
        variants.append(QueryVariant(" ".join(tokens[-2:]), "title_last_two_tokens", 0.60))

    # Keep the original casing query for human-readable traces when possible.
    if title and normalize_text(title) != title.strip().lower():
        variants.append(QueryVariant(normalized_title, "title_normalized", 0.64))
    return variants


def _artist_keyword_variants(artist: str, normalized_artist: str) -> list[QueryVariant]:
    tokens = normalized_artist.split()
    if len(tokens) <= 1:
        return []
    return [
        QueryVariant(tokens[0], "artist_first_token", 0.55),
        QueryVariant(" ".join(tokens[:2]), "artist_first_two_tokens", 0.58),
    ]


def _dedupe(variants: list[QueryVariant]) -> list[QueryVariant]:
    seen: set[str] = set()
    result: list[QueryVariant] = []
    for variant in variants:
        normalized = normalize_text(variant.term)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(variant)
    return result
