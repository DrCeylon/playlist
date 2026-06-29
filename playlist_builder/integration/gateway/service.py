from __future__ import annotations

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalPlaylist
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry


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
