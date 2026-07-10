from __future__ import annotations

from pathlib import Path
from typing import Any

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.integration.ports.provider_auth import ProviderAuthPort
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.ui.shared.dto import ProviderOption
from playlist_builder.ui.shared.dto.provider import default_provider_options
from playlist_builder.integration.youtube_music.secrets import assert_bridge_safe_mapping
from playlist_builder.ui.shared.dto.remote_playlist import ProviderAuthState, RemoteProviderAccount


def _bridge_safe_account_payload(account: RemoteProviderAccount) -> dict[str, Any]:
    payload = account.to_dict()
    assert_bridge_safe_mapping(payload)
    return payload


def provider_options_from_registry(registry: ProviderGatewayRegistry) -> tuple[ProviderOption, ...]:
    options: list[ProviderOption] = []
    for template in default_provider_options():
        gateway = registry.get(template.provider_id)
        if gateway is None:
            options.append(template)
            continue
        options.append(_option_from_gateway(template, gateway))
    return tuple(options)


def _option_from_gateway(template: ProviderOption, gateway: Any) -> ProviderOption:
    auth = getattr(gateway, "auth", None)
    auth_state = auth.auth_state() if isinstance(auth, ProviderAuthPort) else ProviderAuthState.DISCONNECTED
    unavailable_reason = getattr(gateway, "unavailable_reason", lambda: "")()
    is_connected = auth_state == ProviderAuthState.CONNECTED
    is_experimental = ProviderCapability.EXPERIMENTAL in gateway.capabilities

    if template.provider_id == ProviderId.YOUTUBE_MUSIC:
        from playlist_builder.integration.youtube_music.experimental_guard import is_ytmusicapi_installed

        is_available = is_ytmusicapi_installed()
        if not is_available:
            unavailable_reason = unavailable_reason or "Module expérimental non installé."
        return ProviderOption(
            provider_id=template.provider_id,
            display_name=template.display_name,
            is_available=is_available,
            is_connected=is_connected,
            capabilities=gateway.capabilities,
            unavailable_reason=unavailable_reason if not is_available else "",
            is_experimental=True,
        )

    if template.provider_id == ProviderId.APPLE_MUSIC:
        return ProviderOption(
            provider_id=template.provider_id,
            display_name=template.display_name,
            is_available=True,
            is_connected=True,
            capabilities=gateway.capabilities,
            unavailable_reason="",
            is_experimental=False,
        )

    return ProviderOption(
        provider_id=template.provider_id,
        display_name=template.display_name,
        is_available=True,
        is_connected=is_connected,
        capabilities=gateway.capabilities,
        unavailable_reason=unavailable_reason,
        is_experimental=is_experimental,
    )


def provider_auth_status(registry: ProviderGatewayRegistry, *, provider_id: ProviderId) -> dict[str, Any]:
    gateway = registry.get(provider_id)
    if gateway is None:
        raise BridgeError(BridgeErrorCode.PROVIDER_UNAVAILABLE, f"Le fournisseur {provider_id.value} n'est pas disponible.")
    auth = getattr(gateway, "auth", None)
    if not isinstance(auth, ProviderAuthPort):
        raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, f"Authentification non supportée pour {provider_id.value}.")
    state = auth.auth_state()
    display_name = getattr(auth, "account_display_name", lambda: "")()
    account = RemoteProviderAccount(
        provider_id=provider_id,
        display_name=display_name,
        auth_state=state,
        capabilities=gateway.capabilities,
    )
    payload = _bridge_safe_account_payload(account)
    unavailable_reason = getattr(gateway, "unavailable_reason", lambda: "")()
    if unavailable_reason:
        payload["message"] = unavailable_reason
    return {"provider_account": payload}


def provider_connect(registry: ProviderGatewayRegistry, *, provider_id: ProviderId, params: dict[str, Any]) -> dict[str, Any]:
    gateway = registry.get(provider_id)
    if gateway is None:
        raise BridgeError(BridgeErrorCode.PROVIDER_UNAVAILABLE, f"Le fournisseur {provider_id.value} n'est pas disponible.")
    auth = getattr(gateway, "auth", None)
    if not isinstance(auth, ProviderAuthPort):
        raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, f"Authentification non supportée pour {provider_id.value}.")
    connect_params = {str(key): str(value) for key, value in params.items() if isinstance(key, str)}
    try:
        state = auth.connect(params=connect_params)
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, str(exc)) from exc
    display_name = getattr(auth, "account_display_name", lambda: "")()
    account = RemoteProviderAccount(
        provider_id=provider_id,
        display_name=display_name,
        auth_state=state,
        capabilities=gateway.capabilities,
    )
    return {"provider_account": _bridge_safe_account_payload(account)}


def provider_disconnect(registry: ProviderGatewayRegistry, *, provider_id: ProviderId) -> dict[str, Any]:
    gateway = registry.get(provider_id)
    if gateway is None:
        raise BridgeError(BridgeErrorCode.PROVIDER_UNAVAILABLE, f"Le fournisseur {provider_id.value} n'est pas disponible.")
    auth = getattr(gateway, "auth", None)
    if not isinstance(auth, ProviderAuthPort):
        raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, f"Authentification non supportée pour {provider_id.value}.")
    state = auth.disconnect()
    account = RemoteProviderAccount(
        provider_id=provider_id,
        display_name="",
        auth_state=state,
        capabilities=gateway.capabilities,
    )
    return {"provider_account": _bridge_safe_account_payload(account)}


def load_snapshot_from_file(params: dict[str, Any]) -> dict[str, Any]:
    from playlist_builder.app.playlist_library.file_snapshot import load_remote_playlist_snapshot_from_file

    file_path_raw = str(params.get("file_path", "")).strip()
    if not file_path_raw:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "file_path est requis.")
    provider_raw = params.get("provider_id", ProviderId.YOUTUBE_MUSIC.value)
    try:
        provider_id = ProviderId(str(provider_raw))
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"provider_id invalide : {provider_raw!r}") from exc
    snapshot = load_remote_playlist_snapshot_from_file(
        Path(file_path_raw),
        provider_id=provider_id,
        remote_playlist_id=str(params.get("remote_playlist_id", "")).strip(),
        playlist_name=str(params.get("playlist_name", "")).strip(),
    )
    return {"remote_playlist": snapshot.to_dict()}
