from __future__ import annotations

from typing import Any

from playlist_builder.app.playlist_library.import_remote import ImportRemotePlaylist
from playlist_builder.app.playlist_library.migration import HistoryToRepositoryMigration
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.app.bridge_runtime.playlist_sync_plan import remote_snapshot_from_dict
from playlist_builder.ui.shared.dto.playlist_library import (
    PlaylistOrigin,
    PlaylistSyncResult,
)


def list_managed_playlists(
    provider: RepositoryProvider,
    migration: HistoryToRepositoryMigration,
    history_sessions: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    migration.ensure_migrated(history_sessions)
    repository = provider.managed_playlist_repository()
    return tuple(item.summary.to_dict() for item in repository.list_playlists())


def get_managed_playlist(
    provider: RepositoryProvider,
    migration: HistoryToRepositoryMigration,
    history_sessions: tuple[dict[str, Any], ...],
    local_playlist_id: str,
) -> dict[str, Any] | None:
    migration.ensure_migrated(history_sessions)
    playlist_id = str(local_playlist_id).strip()
    if not playlist_id:
        return None
    detail = provider.managed_playlist_repository().get_playlist(playlist_id)
    if detail is None:
        return None
    return {"playlist": detail.to_dict()}


def import_remote_playlist(
    provider: RepositoryProvider,
    params: dict[str, Any],
) -> dict[str, Any]:
    remote_raw = params.get("remote_playlist")
    if not isinstance(remote_raw, dict):
        raise ValueError("remote_playlist est requis.")
    snapshot = remote_snapshot_from_dict({"remote_playlist": remote_raw})
    origin_raw = str(params.get("origin", PlaylistOrigin.PROVIDER_LIBRARY.value)).strip()
    local_playlist_id = str(params.get("local_playlist_id", "")).strip() or None
    use_case = ImportRemotePlaylist(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    )
    detail = use_case.execute(snapshot, origin=origin_raw, local_playlist_id=local_playlist_id)
    return {"playlist": detail.to_dict()}


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
