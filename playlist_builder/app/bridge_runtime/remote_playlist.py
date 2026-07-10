from __future__ import annotations

from typing import Any

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylist, RemotePlaylistSnapshot


def _parse_provider_id(value: object) -> ProviderId:
    try:
        return ProviderId(str(value))
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"provider_id invalide : {value!r}") from exc


def _require_read_port(registry: ProviderGatewayRegistry, provider_id: ProviderId, *, for_list: bool):
    gateway = registry.get(provider_id)
    if gateway is None:
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            f"Le fournisseur {provider_id.value} n'est pas disponible.",
        )
    if for_list:
        if ProviderCapability.PLAYLIST_LIBRARY_BROWSE not in gateway.capabilities:
            raise BridgeError(
                BridgeErrorCode.PROVIDER_UNAVAILABLE,
                f"Le fournisseur {provider_id.value} ne supporte pas la lecture de bibliothèque.",
            )
    elif ProviderCapability.PUBLIC_PLAYLIST_IMPORT not in gateway.capabilities and (
        ProviderCapability.PLAYLIST_LIBRARY_BROWSE not in gateway.capabilities
    ):
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            f"Le fournisseur {provider_id.value} ne supporte pas la lecture de playlists.",
        )
    read_port = gateway.playlist_read
    if read_port is None:
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            f"Le port lecture playlist n'est pas configuré pour {provider_id.value}.",
        )
    return read_port


def list_remote_playlists(
    registry: ProviderGatewayRegistry,
    *,
    provider_id: ProviderId,
    account_id: str | None = None,
) -> tuple[dict[str, Any], ...]:
    read_port = _require_read_port(registry, provider_id, for_list=True)
    playlists = read_port.list_playlists(account_id=account_id)
    return tuple(_remote_playlist_dict(playlist) for playlist in playlists)


def get_remote_playlist(
    registry: ProviderGatewayRegistry,
    *,
    provider_id: ProviderId,
    remote_playlist_id: str,
) -> dict[str, Any]:
    playlist_id = remote_playlist_id.strip()
    if not playlist_id:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "remote_playlist_id est requis.")
    read_port = _require_read_port(registry, provider_id, for_list=False)
    try:
        snapshot = read_port.get_playlist(playlist_id)
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, str(exc)) from exc
    return _remote_playlist_snapshot_dict(snapshot)


def _remote_playlist_dict(playlist: RemotePlaylist) -> dict[str, Any]:
    return playlist.to_dict()


def _remote_playlist_snapshot_dict(snapshot: RemotePlaylistSnapshot) -> dict[str, Any]:
    return snapshot.to_dict()
