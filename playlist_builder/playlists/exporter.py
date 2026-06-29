from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

from playlist_builder.planning.models import EnergyProfile, GeneratedPlaylist
from playlist_builder.session.models import GenerationSession

_GENERIC_SECTIONS = frozenset({"playlist", "discovery", "generated"})

_ENERGY_SECTION_NAMES: dict[EnergyProfile, tuple[str, ...]] = {
    EnergyProfile.RISING: ("🌅 Warm Up", "📈 Rising", "🔥 Peak"),
    EnergyProfile.PARTY: ("🎉 Opening", "💃 Party", "🚀 Finale"),
    EnergyProfile.CHILL: ("🌙 Calm", "☁️ Drift"),
    EnergyProfile.STEADY: ("🎧 Flow",),
    EnergyProfile.MAX_FROM_START: ("⚡ Full Energy",),
}


def export_playlist_dict(generated: GeneratedPlaylist) -> dict:
    """Serialize a generated playlist to JSON compatible with :func:`load_playlist`."""
    request = generated.request
    sections = _build_sections(
        generated,
        default_section_name=request.name.strip() or "Generated",
        energy_profile=request.constraints.energy_profile,
    )

    return {
        "name": request.name,
        "description": request.description,
        "sections": sections,
    }


def export_playlist_json(generated: GeneratedPlaylist, *, indent: int = 2) -> str:
    return json.dumps(export_playlist_dict(generated), ensure_ascii=False, indent=indent) + "\n"


def write_generated_playlist(
    generated: GeneratedPlaylist,
    path: Path,
    *,
    indent: int = 2,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(export_playlist_json(generated, indent=indent), encoding="utf-8")
    return path


def write_session_playlist(
    session: GenerationSession,
    path: Path,
    *,
    indent: int = 2,
) -> Path:
    return write_generated_playlist(session.generated_playlist, path, indent=indent)


def _build_sections(
    generated: GeneratedPlaylist,
    *,
    default_section_name: str,
    energy_profile: EnergyProfile,
) -> list[dict]:
    candidates = list(generated.candidates)
    if not candidates:
        return [{"name": default_section_name, "songs": []}]

    if _uses_generic_sections(candidates):
        tier_names = _ENERGY_SECTION_NAMES.get(energy_profile)
        if tier_names and len(tier_names) > 1 and len(candidates) >= len(tier_names):
            return _split_into_tiers(candidates, tier_names)

    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for candidate in candidates:
        section_name = _section_name(candidate.track.section, default_section_name)
        grouped.setdefault(section_name, []).append(
            {
                "artist": candidate.track.artist,
                "title": candidate.track.title,
            }
        )

    return [{"name": name, "songs": songs} for name, songs in grouped.items()]


def _uses_generic_sections(candidates) -> bool:
    return all(
        not candidate.track.section.strip()
        or candidate.track.section.strip().lower() in _GENERIC_SECTIONS
        for candidate in candidates
    )


def _split_into_tiers(candidates, tier_names: tuple[str, ...]) -> list[dict]:
    tier_count = len(tier_names)
    chunk_size = max(1, len(candidates) // tier_count)
    sections: list[dict] = []

    for index, name in enumerate(tier_names):
        start = index * chunk_size
        end = len(candidates) if index == tier_count - 1 else (index + 1) * chunk_size
        tier_candidates = candidates[start:end]
        if not tier_candidates:
            continue
        sections.append(
            {
                "name": name,
                "songs": [
                    {"artist": candidate.track.artist, "title": candidate.track.title}
                    for candidate in tier_candidates
                ],
            }
        )

    return sections or [{"name": tier_names[0], "songs": []}]


def _section_name(section: str, default_section_name: str) -> str:
    cleaned = section.strip()
    if not cleaned or cleaned.lower() in _GENERIC_SECTIONS:
        return default_section_name
    return cleaned
