from __future__ import annotations

from typing import Any

from playlist_builder.app.bridge_runtime.playlist_sync_plan import _load_remote_snapshot, remote_snapshot_from_dict
from playlist_builder.app.playlist_sync.apply import ApplySyncPlaylist, ApplySyncRequest
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode


def apply_sync(
    registry: ProviderGatewayRegistry,
    provider: RepositoryProvider,
    *,
    params: dict[str, Any],
    local_playlist_id: str,
) -> dict[str, Any]:
    provider_raw = params.get("provider_id", ProviderId.APPLE_MUSIC.value)
    try:
        provider_id = ProviderId(str(provider_raw))
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"provider_id invalide : {provider_raw!r}") from exc

    direction_raw = str(params.get("direction", SyncDirection.PUSH_TO_PROVIDER.value))
    try:
        direction = SyncDirection(direction_raw)
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"direction invalide : {direction_raw!r}") from exc

    mode_raw = str(params.get("sync_mode", SyncMode.APPEND_ONLY.value))
    try:
        sync_mode = SyncMode(mode_raw)
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"sync_mode invalide : {mode_raw!r}") from exc

    plan_checksum_value = str(params.get("plan_checksum", "")).strip()
    if not plan_checksum_value:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "plan_checksum est requis.")

    expected_version = int(params.get("expected_local_playlist_version", 0) or 0)
    expected_remote_checksum = str(params.get("expected_remote_snapshot_checksum", "")).strip()
    if not expected_remote_checksum:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "expected_remote_snapshot_checksum est requis.")

    playlist_repo = provider.managed_playlist_repository()
    local = playlist_repo.get_playlist(local_playlist_id)
    if local is None:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "Playlist locale introuvable.")

    remote_snapshot = None
    if isinstance(params.get("remote_playlist"), dict):
        remote_snapshot = remote_snapshot_from_dict({"remote_playlist": params["remote_playlist"]})
    remote_playlist_id = str(params.get("remote_playlist_id", "")).strip()
    if remote_snapshot is None:
        if not remote_playlist_id:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "remote_playlist_id ou remote_playlist est requis.")
        remote_snapshot = _load_remote_snapshot(registry, provider_id, remote_playlist_id)

    gateway = registry.get(provider_id)
    if gateway is None:
        raise BridgeError(BridgeErrorCode.PROVIDER_UNAVAILABLE, f"Le fournisseur {provider_id.value} n'est pas disponible.")

    write_port = gateway.playlist_write
    capabilities = gateway.capabilities

    use_case = ApplySyncPlaylist(
        playlist_repository=playlist_repo,
        operation_repository=provider.sync_operation_repository(),
    )
    request = ApplySyncRequest(
        local_playlist_id=local_playlist_id,
        provider_id=provider_id,
        direction=direction,
        sync_mode=sync_mode,
        confirm_destructive=bool(params.get("confirm_destructive", False)),
        expected_local_playlist_version=expected_version,
        expected_remote_snapshot_checksum=expected_remote_checksum,
        plan_checksum=plan_checksum_value,
        remote_playlist_id=remote_snapshot.remote_playlist_id,
    )
    result = use_case.execute(
        request,
        local=local,
        remote=remote_snapshot,
        write_port=write_port,
        provider_capabilities=capabilities,
    )
    return {"sync_apply": result.to_dict()}
