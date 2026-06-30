from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.canonical.models import (
    CanonicalImportReport,
    CanonicalPlaylist,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
)
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry


@dataclass(frozen=True, slots=True)
class IncrementalImportContext:
    """Provider-prepared state for incremental playlist imports."""

    existing_keys: set[str] | None


class IntegrationGateway:
    """Generic integration gateway routing canonical operations to provider gateways."""

    def __init__(self, registry: ProviderGatewayRegistry) -> None:
        self._registry = registry

    def import_playlist(
        self,
        playlist: CanonicalPlaylist,
        *,
        provider_id: ProviderId = ProviderId.APPLE_MUSIC,
        sync: bool = True,
        existing_keys: set[str] | None = None,
        allow_duplicates: bool = False,
    ) -> CanonicalImportReport:
        gateway = self._registry.require(provider_id)
        if ProviderCapability.PLAYLIST_DELIVERY not in gateway.capabilities:
            raise ValueError(f"Provider {provider_id.value} does not support playlist delivery.")
        if gateway.delivery is None:
            raise ValueError(f"Provider {provider_id.value} has no delivery adapter configured.")

        if sync:
            return gateway.delivery.import_playlist(playlist)

        import_service = getattr(gateway, "import_service", None)
        if import_service is None:
            raise ValueError(
                f"Provider {provider_id.value} incremental import requires an import service."
            )
        return import_service.import_playlist(
            playlist,
            sync=False,
            existing_keys=existing_keys,
            allow_duplicates=allow_duplicates,
        )

    def prepare_incremental_import(
        self,
        playlist_name: str,
        *,
        provider_id: ProviderId = ProviderId.APPLE_MUSIC,
        allow_duplicates: bool = False,
    ) -> IncrementalImportContext:
        """Ensure the target playlist exists and return keys already present."""
        gateway = self._registry.require(provider_id)
        import_service = getattr(gateway, "import_service", None)
        if import_service is None:
            raise ValueError(
                f"Provider {provider_id.value} incremental import requires an import service."
            )

        applescript = getattr(import_service, "applescript", None)
        if applescript is None:
            raise ValueError(
                f"Provider {provider_id.value} incremental import requires a runtime client."
            )

        applescript.ensure_running()
        applescript.ensure_playlist(playlist_name)
        existing_keys = None if allow_duplicates else applescript.load_playlist_keys(playlist_name)
        return IncrementalImportContext(existing_keys=existing_keys)

    def search_catalog(
        self,
        request: CanonicalSearchRequest,
        *,
        provider_id: ProviderId = ProviderId.APPLE_MUSIC,
    ) -> CanonicalSearchResponse:
        gateway = self._registry.require(provider_id)
        if ProviderCapability.CATALOG_SEARCH not in gateway.capabilities:
            raise ValueError(f"Provider {provider_id.value} does not support catalog search.")
        if gateway.catalog is None:
            raise ValueError(f"Provider {provider_id.value} has no catalog adapter configured.")
        return gateway.catalog.search(request)

    def flush_caches(
        self,
        *,
        provider_id: ProviderId = ProviderId.APPLE_MUSIC,
        flush_catalog_cache: bool = True,
    ) -> None:
        gateway = self._registry.require(provider_id)
        import_service = getattr(gateway, "import_service", None)
        if import_service is not None:
            identity_cache = getattr(import_service, "identity_cache", None)
            if identity_cache is not None:
                identity_cache.flush()

        if not flush_catalog_cache:
            return

        catalog = gateway.catalog
        if catalog is None:
            return
        client = getattr(catalog, "client", None)
        if client is None:
            return
        cache = getattr(client, "cache", None)
        if cache is not None:
            cache.flush()
