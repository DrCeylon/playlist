from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.core.models import TrackRef
from playlist_builder.resolver.constants import MAX_QUERY_VARIANTS, _GENERIC_SECTIONS
from playlist_builder.resolver.normalization import normalize_text

_CONTEXT_ALIASES: tuple[tuple[tuple[str, ...], tuple[tuple[str, float], ...]], ...] = (
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


@dataclass(frozen=True)
class QueryVariant:
    term: str
    reason: str
    weight: float = 1.0


def generate_query_variants(track: TrackRef) -> list[QueryVariant]:
    """Generate ordered search variants for Apple Music/library lookup."""

    title = track.title.strip()
    artist = track.artist.strip()
    section = track.section.strip()

    raw_variants = [
        QueryVariant(f"{title} {artist}", "title_artist", 1.0),
        QueryVariant(f"{artist} {title}", "artist_title", 0.95),
        QueryVariant(title, "title", 0.85),
    ]

    normalized_title = normalize_text(title)
    for tokens, aliases in _CONTEXT_ALIASES:
        if any(token in normalized_title for token in tokens):
            for term_template, reason, weight in aliases:
                raw_variants.append(QueryVariant(term_template.format(title=title), reason, weight))

    if section and normalize_text(section) not in _GENERIC_SECTIONS:
        raw_variants.extend(
            [
                QueryVariant(f"{section} {title}", "section_title", 0.78),
                QueryVariant(f"{title} {section}", "title_section", 0.76),
            ]
        )

    return _dedupe(raw_variants)[:MAX_QUERY_VARIANTS]


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
