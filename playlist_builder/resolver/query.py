from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.core.models import TrackRef
from playlist_builder.resolver.normalization import normalize_text


@dataclass(frozen=True)
class QueryVariant:
    term: str
    reason: str
    weight: float = 1.0


def generate_query_variants(track: TrackRef) -> list[QueryVariant]:
    """Generate ordered search variants for Apple Music/library lookup.

    The order goes from most precise to broadest. Variants are deduplicated after
    normalization so the AppleScript layer does not waste time on equivalent
    queries.
    """

    title = track.title.strip()
    artist = track.artist.strip()
    section = track.section.strip()

    raw_variants = [
        QueryVariant(f"{title} {artist}", "title_artist", 1.0),
        QueryVariant(f"{artist} {title}", "artist_title", 0.95),
        QueryVariant(title, "title", 0.85),
    ]

    if section and normalize_text(section) not in {"playlist", "generated", "discovery"}:
        raw_variants.extend(
            [
                QueryVariant(f"{section} {title}", "section_title", 0.78),
                QueryVariant(f"{title} {section}", "title_section", 0.76),
            ]
        )

    # Helpful game/OST aliases for the first real-world use case. These are not
    # hard-coded matches, only search hints with lower weight.
    normalized_title = normalize_text(title)
    if any(token in normalized_title for token in ("gerudo", "zelda")):
        raw_variants.extend(
            [
                QueryVariant(f"Zelda {title}", "alias_zelda_title", 0.72),
                QueryVariant(f"Legend of Zelda {title}", "alias_legend_of_zelda_title", 0.70),
            ]
        )
    if "mario" in normalized_title:
        raw_variants.append(QueryVariant(f"Nintendo {title}", "alias_nintendo_title", 0.70))

    return _dedupe(raw_variants)


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
