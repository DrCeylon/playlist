from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from playlist_builder.core.models import PlaylistDefinition
from playlist_builder.integration.ports.provider_import import (
    ProviderImportResolutionOutcome,
    ProviderImportResolutionStatus,
)


@dataclass(frozen=True, slots=True)
class CheckpointResolvedOutcome:
    """Serializable resolution outcome captured before a manual-acquisition pause."""

    artist: str
    title: str
    section: str
    status: str
    cache_hit: bool = False
    catalog_acquired: bool = False
    error: str = ""


@dataclass(slots=True)
class ImportSessionCheckpoint:
    session_id: str
    playlist: PlaylistDefinition
    next_index: int
    request_id: str
    sync: bool
    write_json_diagnostics: bool
    history_session_id: str = ""
    resolved_outcomes: tuple[CheckpointResolvedOutcome, ...] = ()


class ImportSessionStore:
    """Persists in-flight imports so Resonance can resume after manual acquisition."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path("data/imports/checkpoints")
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
            "history_session_id": checkpoint.history_session_id,
            "resolved_outcomes": [
                {
                    "artist": item.artist,
                    "title": item.title,
                    "section": item.section,
                    "status": item.status,
                    "cache_hit": item.cache_hit,
                    "catalog_acquired": item.catalog_acquired,
                    "error": item.error,
                }
                for item in checkpoint.resolved_outcomes
            ],
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
        resolved_outcomes = tuple(
            CheckpointResolvedOutcome(
                artist=str(item.get("artist", "")),
                title=str(item.get("title", "")),
                section=str(item.get("section", "Playlist")),
                status=str(item.get("status", ProviderImportResolutionStatus.NOT_FOUND.value)),
                cache_hit=bool(item.get("cache_hit", False)),
                catalog_acquired=bool(item.get("catalog_acquired", False)),
                error=str(item.get("error", "")),
            )
            for item in payload.get("resolved_outcomes", [])
            if isinstance(item, dict)
        )
        return ImportSessionCheckpoint(
            session_id=payload["session_id"],
            playlist=playlist,
            next_index=int(payload.get("next_index", 0)),
            request_id=str(payload.get("request_id", session_id)),
            sync=bool(payload.get("sync", True)),
            write_json_diagnostics=bool(payload.get("write_json_diagnostics", True)),
            history_session_id=str(payload.get("history_session_id", "")),
            resolved_outcomes=resolved_outcomes,
        )

    def path_for(self, session_id: str) -> Path:
        return self._root / f"{session_id}.json"

    def exists(self, session_id: str) -> bool:
        return self.path_for(session_id).exists()

    def delete(self, session_id: str) -> None:
        path = self.path_for(session_id)
        if path.exists():
            path.unlink()


def new_session_id() -> str:
    return uuid.uuid4().hex


def checkpoint_outcomes_from_provider_pairs(
    outcomes: list[tuple[ProviderImportResolutionOutcome, str]],
) -> tuple[CheckpointResolvedOutcome, ...]:
    stored: list[CheckpointResolvedOutcome] = []
    for outcome, section_name in outcomes:
        stored.append(
            CheckpointResolvedOutcome(
                artist=outcome.track.artist.name,
                title=outcome.track.title,
                section=section_name,
                status=outcome.status.value,
                cache_hit=outcome.cache_hit,
                catalog_acquired=outcome.catalog_acquired,
                error=outcome.error,
            )
        )
    return tuple(stored)


def provider_pairs_from_checkpoint_outcomes(
    stored: tuple[CheckpointResolvedOutcome, ...],
    rows: list[tuple],
) -> list[tuple[ProviderImportResolutionOutcome, str]]:
    pairs: list[tuple[ProviderImportResolutionOutcome, str]] = []
    for index, item in enumerate(stored):
        if index >= len(rows):
            break
        track, default_section = rows[index]
        section_name = item.section or default_section
        try:
            status = ProviderImportResolutionStatus(item.status)
        except ValueError:
            status = ProviderImportResolutionStatus.ERROR
        pairs.append(
            (
                ProviderImportResolutionOutcome(
                    track=track,
                    status=status,
                    cache_hit=item.cache_hit,
                    catalog_acquired=item.catalog_acquired,
                    error=item.error,
                ),
                section_name,
            )
        )
    return pairs


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
