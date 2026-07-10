from __future__ import annotations

from typing import Any

from playlist_builder.app.playlist_library.repository import ManagedPlaylistRepository
from playlist_builder.ui.shared.dto.playlist_library import (
    ManagedPlaylistDetail,
    ManagedPlaylistTrack,
    managed_playlist_from_history_session,
)


class HistoryToRepositoryMigration:
    """Lazy, idempotent migration from session history into the managed playlist repository."""

    def __init__(self, repository: ManagedPlaylistRepository) -> None:
        self._repository = repository

    def ensure_migrated(self, history_sessions: tuple[dict[str, Any], ...]) -> None:
        existing_ids = {item.summary.local_playlist_id for item in self._repository.list_playlists()}
        ordered = sorted(
            history_sessions,
            key=lambda session: str(session.get("started_at_iso", "")),
        )
        for session in ordered:
            summary = managed_playlist_from_history_session(session)
            if summary is None:
                continue
            if summary.local_playlist_id in existing_ids:
                continue
            tracks = _tracks_from_history_session(session, summary.local_playlist_id)
            detail = ManagedPlaylistDetail(summary=summary, tracks=tracks)
            self._repository.upsert(detail)
            existing_ids.add(summary.local_playlist_id)


def _tracks_from_history_session(
    session: dict[str, Any],
    local_playlist_id: str,
) -> tuple[ManagedPlaylistTrack, ...]:
    import_result = session.get("import_result")
    if not isinstance(import_result, dict):
        return ()
    outcomes = import_result.get("outcomes", [])
    if not isinstance(outcomes, list):
        return ()
    tracks: list[ManagedPlaylistTrack] = []
    for index, item in enumerate(outcomes):
        if not isinstance(item, dict):
            continue
        artist = str(item.get("artist", "")).strip()
        title = str(item.get("title", "")).strip()
        if not artist or not title:
            continue
        status = str(item.get("status", "")).strip().lower()
        mapping = "matched" if status == "added" else "missing_on_provider" if status == "not_found" else "unresolved"
        tracks.append(
            ManagedPlaylistTrack(
                local_track_id=f"{local_playlist_id}-tr-{index}",
                artist=artist,
                title=title,
                section=str(item.get("section", "")),
                mapping_status=mapping,
            )
        )
    return tuple(tracks)
