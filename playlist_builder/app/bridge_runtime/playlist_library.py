from __future__ import annotations

from typing import Any

from playlist_builder.ui.shared.dto.playlist_library import (
    ManagedPlaylistDetail,
    ManagedPlaylistSummary,
    PlaylistSyncResult,
    managed_playlist_from_history_session,
)


def list_managed_playlists_from_history(sessions: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    playlists: list[dict[str, Any]] = []
    for session in sessions:
        summary = managed_playlist_from_history_session(session)
        if summary is not None:
            playlists.append(summary.to_dict())
    return tuple(playlists)


def managed_playlist_detail(backend: Any, local_playlist_id: str) -> dict[str, Any] | None:
    playlist_id = str(local_playlist_id).strip()
    if not playlist_id:
        return None
    for session in backend.list_history():
        summary = managed_playlist_from_history_session(session)
        if summary is None or summary.local_playlist_id != playlist_id:
            continue
        detail = ManagedPlaylistDetail(summary=summary, tracks=())
        return {"playlist": detail.to_dict()}
    return None


def sync_managed_playlist_stub(params: dict[str, Any]) -> dict[str, Any]:
    playlist_id = str(params.get("local_playlist_id", "")).strip()
    provider_id = str(params.get("provider_id", "")).strip()
    message = (
        "Synchronisation en file d'attente — gateway provider "
        f"{provider_id or 'inconnu'} en cours d'intégration."
    )
    result = PlaylistSyncResult(
        local_playlist_id=playlist_id,
        sync_status="pending",
        message=message,
    )
    return {"sync": result.to_dict()}
