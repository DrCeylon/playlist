from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

from playlist_builder.planning.models import GeneratedPlaylist
from playlist_builder.session.models import GenerationSession

_GENERIC_SECTIONS = frozenset({"playlist", "discovery", "generated"})


def export_playlist_dict(generated: GeneratedPlaylist) -> dict:
    """Serialize a generated playlist to JSON compatible with :func:`load_playlist`."""
    request = generated.request
    sections = _build_sections(generated, default_section_name=request.name.strip() or "Generated")

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


def _build_sections(generated: GeneratedPlaylist, *, default_section_name: str) -> list[dict]:
    grouped: OrderedDict[str, list[dict]] = OrderedDict()

    for candidate in generated.candidates:
        section_name = _section_name(candidate.track.section, default_section_name)
        grouped.setdefault(section_name, []).append(
            {
                "artist": candidate.track.artist,
                "title": candidate.track.title,
            }
        )

    if not grouped:
        return [{"name": default_section_name, "songs": []}]

    return [{"name": name, "songs": songs} for name, songs in grouped.items()]


def _section_name(section: str, default_section_name: str) -> str:
    cleaned = section.strip()
    if not cleaned or cleaned.lower() in _GENERIC_SECTIONS:
        return default_section_name
    return cleaned
