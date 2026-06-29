from __future__ import annotations

import json
from pathlib import Path

from playlist_builder.core.models import TrackRef


class PlaylistValidationError(ValueError):
    pass


def _require_text_field(item: dict, field: str, *, section: str, index: int) -> str:
    if field not in item:
        raise PlaylistValidationError(
            f"Champ manquant '{field}' pour le morceau #{index + 1} dans la section '{section}'."
        )
    value = item[field]
    if not isinstance(value, str):
        raise PlaylistValidationError(
            f"Le champ '{field}' doit être une chaîne pour le morceau #{index + 1} "
            f"dans la section '{section}'."
        )
    cleaned = value.strip()
    if not cleaned:
        raise PlaylistValidationError(
            f"Le champ '{field}' est vide pour le morceau #{index + 1} dans la section '{section}'."
        )
    return cleaned


def load_playlist(path: Path) -> tuple[str, list[TrackRef]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PlaylistValidationError(f"JSON invalide dans {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise PlaylistValidationError("La playlist doit être un objet JSON.")

    playlist_name = data.get("name")
    if not isinstance(playlist_name, str) or not playlist_name.strip():
        raise PlaylistValidationError("Le champ 'name' est requis et ne peut pas être vide.")

    sections = data.get("sections", [])
    if not isinstance(sections, list):
        raise PlaylistValidationError("Le champ 'sections' doit être une liste.")

    tracks: list[TrackRef] = []
    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise PlaylistValidationError(f"La section #{section_index + 1} doit être un objet JSON.")

        section_name = section.get("name", "Playlist")
        if not isinstance(section_name, str) or not section_name.strip():
            section_name = "Playlist"

        songs = section.get("songs", [])
        if not isinstance(songs, list):
            raise PlaylistValidationError(
                f"Le champ 'songs' de la section '{section_name}' doit être une liste."
            )

        for song_index, item in enumerate(songs):
            if not isinstance(item, dict):
                raise PlaylistValidationError(
                    f"Le morceau #{song_index + 1} de la section '{section_name}' doit être un objet JSON."
                )
            tracks.append(
                TrackRef(
                    artist=_require_text_field(item, "artist", section=section_name, index=song_index),
                    title=_require_text_field(item, "title", section=section_name, index=song_index),
                    section=section_name.strip(),
                )
            )

    return playlist_name.strip(), tracks
