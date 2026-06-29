from __future__ import annotations

import json
from pathlib import Path

from playlist_builder.core.models import TrackRef


def load_playlist(path: Path) -> tuple[str, list[TrackRef]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tracks: list[TrackRef] = []
    for section in data.get("sections", []):
        section_name = section.get("name", "Playlist")
        for item in section.get("songs", []):
            tracks.append(TrackRef(artist=item["artist"], title=item["title"], section=section_name))
    return data["name"], tracks
