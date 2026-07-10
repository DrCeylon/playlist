from __future__ import annotations

from pathlib import Path
from typing import Any

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.canonical.provider_ids import provider_display_name
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
    templates = {template.provider_id: template for template in default_provider_options()}
    options: list[ProviderOption] = []
    seen: set[ProviderId] = set()

    for provider_id in registry.list_provider_ids():
        gateway = registry.require(provider_id)
        template = templates.get(
            provider_id,
            ProviderOption(
                provider_id=provider_id,
                display_name=provider_display_name(provider_id),
                is_available=False,
            ),
        )
        options.append(_option_from_gateway(template, gateway))
        seen.add(provider_id)

    for template in default_provider_options():
        if template.provider_id in seen:
            continue
        options.append(template)

    return tuple(options)


def _option_from_gateway(template: ProviderOption, gateway: Any) -> ProviderOption:
    auth = getattr(gateway, "auth", None)
    unavailable_reason = getattr(gateway, "unavailable_reason", lambda: "")()
    is_experimental = ProviderCapability.EXPERIMENTAL in gateway.capabilities

    if isinstance(auth, ProviderAuthPort):
        is_connected = auth.auth_state() == ProviderAuthState.CONNECTED
    elif getattr(gateway, "implicit_auth_connected", False):
        is_connected = True
    else:
        is_connected = False

    is_available = not unavailable_reason

    return ProviderOption(
        provider_id=template.provider_id,
        display_name=template.display_name,
        is_available=is_available,
        is_connected=is_connected and is_available,
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
    from playlist_builder.canonical.provider_ids import parse_provider_id

    file_path_raw = str(params.get("file_path", "")).strip()
    if not file_path_raw:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "file_path est requis.")
    try:
        provider_id = parse_provider_id(params.get("provider_id"), default=ProviderId.YOUTUBE_MUSIC)
    except ValueError as exc:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, str(exc)) from exc
    snapshot = load_remote_playlist_snapshot_from_file(
        Path(file_path_raw),
        provider_id=provider_id,
        remote_playlist_id=str(params.get("remote_playlist_id", "")).strip(),
        playlist_name=str(params.get("playlist_name", "")).strip(),
    )
    return {"remote_playlist": snapshot.to_dict()}
