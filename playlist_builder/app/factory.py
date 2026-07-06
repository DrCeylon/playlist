from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.app.settings import AppSettings
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
from playlist_builder.integration.apple_music.gateway import AppleMusicProviderGateway, build_apple_music_gateway
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.integration.gateway.service import IntegrationGateway
from playlist_builder.integration.ports.provider_import import ProviderImportPort
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.infrastructure.manual_continue_trace import log as manual_continue_trace


def get_provider_import_port(
    context: AppContext,
    provider_id: ProviderId = ProviderId.APPLE_MUSIC,
) -> ProviderImportPort:
    """Resolve a streaming import port for the requested provider."""
    manual_continue_trace(f"ENTER get_provider_import_port(provider_id={provider_id.value})")
    gateway = context.registry.get(provider_id)
    if gateway is None:
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            f"Le fournisseur {provider_id.value} n'est pas disponible.",
        )

    import_service = getattr(gateway, "import_service", None)
    if import_service is None:
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            f"Le fournisseur {provider_id.value} ne supporte pas l'import streamé.",
        )

    if provider_id == ProviderId.APPLE_MUSIC:
        from playlist_builder.integration.apple_music.provider_import_port import AppleMusicProviderImportPort

        port = AppleMusicProviderImportPort(import_service)
        manual_continue_trace(f"RETURN get_provider_import_port -> AppleMusicProviderImportPort")
        return port

    raise BridgeError(
        BridgeErrorCode.PROVIDER_UNAVAILABLE,
        f"Aucun ProviderImportPort enregistré pour {provider_id.value}.",
    )


@dataclass(frozen=True, slots=True)
class AppContext:
    """Composition root for CLI and future UI entry points."""

    settings: AppSettings
    registry: ProviderGatewayRegistry
    gateway: IntegrationGateway

    @property
    def apple_music(self) -> AppleMusicProviderGateway:
        """Provider-specific accessor for tests and Apple Music extensions only."""
        return self.registry.require(ProviderId.APPLE_MUSIC)


def build_app_context(settings: AppSettings | None = None) -> AppContext:
    config = settings or AppSettings()
    catalog_cache = JsonCache(config.catalog_cache_path) if config.use_catalog_cache else None
    identity_cache = IdentityCache(JsonCache(config.identity_cache_path))
    registry = ProviderGatewayRegistry()
    apple_gateway = build_apple_music_gateway(
        country=config.country_code,
        cache=catalog_cache,
        identity_cache=identity_cache,
        acquire_missing=config.acquire_missing_from_catalog,
        wait_for_manual_catalog_add=config.wait_for_manual_catalog_add,
        catalog_acquisition_min_confidence=config.catalog_acquisition_min_confidence,
    )
    registry.register(apple_gateway)
    return AppContext(
        settings=config,
        registry=registry,
        gateway=IntegrationGateway(registry),
    )
