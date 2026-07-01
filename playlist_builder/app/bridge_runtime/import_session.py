from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import gettempdir

from playlist_builder.core.models import PlaylistDefinition


@dataclass(slots=True)
class ImportSessionCheckpoint:
    session_id: str
    playlist: PlaylistDefinition
    next_index: int
    request_id: str
    sync: bool
    write_json_diagnostics: bool


class ImportSessionStore:
    """Persists in-flight imports so Resonance can resume after manual acquisition."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(gettempdir()) / "resonance_bridge_imports"
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: ImportSessionCheckpoint) -> str:
        path = self._root / f"{checkpoint.session_id}.json"
        payload = {
            "session_id": checkpoint.session_id,
            "playlist": _playlist_to_dict(checkpoint.playlist),
            "next_index": checkpoint.next_index,
            "request_id": checkpoint.request_id,
            "sync": checkpoint.sync,
            "write_json_diagnostics": checkpoint.write_json_diagnostics,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return checkpoint.session_id

    def load(self, session_id: str) -> ImportSessionCheckpoint | None:
        path = self._root / f"{session_id}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        playlist_data = payload["playlist"]
        sections = []
        for section in playlist_data.get("sections", []):
            from playlist_builder.core.models import PlaylistSection, TrackRef

            tracks = tuple(
                TrackRef(
                    artist=song.get("artist", ""),
                    title=song.get("title", ""),
                    section=section.get("name", "Playlist"),
                )
                for song in section.get("tracks", section.get("songs", []))
            )
            sections.append(PlaylistSection(name=section.get("name", "Playlist"), tracks=tracks))
        playlist = PlaylistDefinition(
            name=playlist_data.get("name", ""),
            sections=tuple(sections),
            description=playlist_data.get("description", ""),
        )
        return ImportSessionCheckpoint(
            session_id=payload["session_id"],
            playlist=playlist,
            next_index=int(payload.get("next_index", 0)),
            request_id=str(payload.get("request_id", session_id)),
            sync=bool(payload.get("sync", True)),
            write_json_diagnostics=bool(payload.get("write_json_diagnostics", True)),
        )

    def delete(self, session_id: str) -> None:
        path = self._root / f"{session_id}.json"
        if path.exists():
            path.unlink()


def new_session_id() -> str:
    return uuid.uuid4().hex


def _playlist_to_dict(playlist: PlaylistDefinition) -> dict[str, object]:
    return {
        "name": playlist.name,
        "description": playlist.description,
        "sections": [
            {
                "name": section.name,
                "tracks": [
                    {"artist": track.artist, "title": track.title, "section": track.section}
                    for track in section.tracks
                ],
            }
            for section in playlist.sections
        ],
    }
