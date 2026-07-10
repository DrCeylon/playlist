from __future__ import annotations

from typing import Any

from playlist_builder.app.playlist_sync.resolve_conflicts import ConflictResolution, ResolveSyncConflicts, ResolveSyncConflictsRequest
from playlist_builder.app.bridge_runtime.playlist_sync_plan import managed_playlist_detail_from_dict, remote_snapshot_from_dict
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode


def resolve_sync_conflicts(
    *,
    params: dict[str, Any],
    local_detail: Any,
    remote_snapshot: Any,
) -> dict[str, Any]:
    direction_raw = str(params.get("direction", SyncDirection.PULL_FROM_PROVIDER.value))
    mode_raw = str(params.get("sync_mode", SyncMode.MANUAL_RESOLVE.value))
    try:
        direction = SyncDirection(direction_raw)
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"direction invalide : {direction_raw!r}") from exc
    try:
        sync_mode = SyncMode(mode_raw)
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"sync_mode invalide : {mode_raw!r}") from exc

    resolutions_raw = params.get("resolutions", [])
    if not isinstance(resolutions_raw, list) or not resolutions_raw:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "resolutions est requis (liste non vide).")

    resolutions: list[ConflictResolution] = []
    for item in resolutions_raw:
        if not isinstance(item, dict):
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "Chaque résolution doit être un objet.")
        try:
            resolutions.append(ConflictResolution.from_dict(item))
        except ValueError as exc:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, str(exc)) from exc

    provider_raw = params.get("provider_id", ProviderId.APPLE_MUSIC.value)
    try:
        provider_id = ProviderId(str(provider_raw))
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"provider_id invalide : {provider_raw!r}") from exc

    local_playlist_id = str(params.get("local_playlist_id", "")).strip()
    remote_playlist_id = str(params.get("remote_playlist_id", remote_snapshot.remote_playlist_id)).strip()
    if not local_playlist_id:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "local_playlist_id est requis.")

    use_case = ResolveSyncConflicts()
    try:
        result = use_case.execute(
            ResolveSyncConflictsRequest(
                local_playlist_id=local_playlist_id,
                provider_id=provider_id.value,
                direction=direction,
                sync_mode=sync_mode,
                remote_playlist_id=remote_playlist_id,
                resolutions=tuple(resolutions),
            ),
            local=local_detail,
            remote=remote_snapshot,
        )
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, str(exc)) from exc

    payload = result.to_dict()
    payload["sync_resolve"] = {
        "remaining_conflicts": result.remaining_conflicts,
        "message": result.message,
    }
    return payload
