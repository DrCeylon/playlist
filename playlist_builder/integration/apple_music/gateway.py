from __future__ import annotations

from pathlib import Path

from playlist_builder.canonical.contracts import CatalogSearchPort, PlaylistDeliveryPort, ProviderGateway
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalPlaylist
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.catalog_gateway import AppleCatalogGateway
from playlist_builder.integration.apple_music.import_service import AppleMusicImportService
from playlist_builder.integration.apple_music.itunes_client import ITunesSearchClient
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry


class AppleMusicDeliveryGateway(PlaylistDeliveryPort):
    """Playlist delivery port backed by the Apple Music import service."""

    def __init__(self, import_service: AppleMusicImportService) -> None:
        self._import_service = import_service

    def import_playlist(self, playlist: CanonicalPlaylist) -> CanonicalImportReport:
        return self._import_service.import_playlist(playlist, sync=True)


class AppleMusicProviderGateway(ProviderGateway):
    """Apple Music provider gateway exposing catalog search and playlist delivery."""

    def __init__(
        self,
        catalog: AppleCatalogGateway,
        import_service: AppleMusicImportService,
    ) -> None:
        self._catalog = catalog
        self._import_service = import_service
        self._delivery = AppleMusicDeliveryGateway(import_service)

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.APPLE_MUSIC

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        return frozenset(
            {
                ProviderCapability.CATALOG_SEARCH,
                ProviderCapability.LIBRARY_RESOLVE,
                ProviderCapability.PLAYLIST_DELIVERY,
            }
        )

    @property
    def catalog(self) -> AppleCatalogGateway:
        return self._catalog

    @property
    def library(self) -> AppleMusicImportService:
        return self._import_service

    @property
    def delivery(self) -> AppleMusicDeliveryGateway:
        return self._delivery

    @property
    def playlist_read(self) -> None:
        return None

    @property
    def playlist_write(self) -> None:
        return None

    @property
    def import_service(self) -> AppleMusicImportService:
        return self._import_service


def build_apple_music_gateway(
    *,
    country: str = "us",
    cache=None,
    rate_limiter=None,
    retry_policy=None,
    identity_cache: IdentityCache | None = None,
    applescript: AppleScriptClient | None = None,
    acquire_missing: bool = True,
    wait_for_manual_catalog_add: bool = False,
    catalog_acquisition_min_confidence: float = 70.0,
) -> AppleMusicProviderGateway:
    client = ITunesSearchClient(
        country=country,
        cache=cache,
        rate_limiter=rate_limiter,
        retry_policy=retry_policy,
    )
    script_client = applescript or AppleScriptClient()
    catalog_gateway = AppleCatalogGateway(client)
    import_service = AppleMusicImportService(
        script_client,
        identity_cache or IdentityCache(JsonCache(Path("cache/apple_music_identity.json"))),
        catalog=catalog_gateway,
        country_code=country,
        acquire_missing=acquire_missing,
        wait_for_manual_catalog_add=wait_for_manual_catalog_add,
        catalog_acquisition_min_confidence=catalog_acquisition_min_confidence,
    )
    return AppleMusicProviderGateway(catalog_gateway, import_service)


def build_apple_music_import_service(
    *,
    identity_cache_path: Path | None = None,
    applescript: AppleScriptClient | None = None,
    catalog: CatalogSearchPort | None = None,
    country_code: str = "us",
    acquire_missing: bool = True,
    wait_for_manual_catalog_add: bool = False,
    catalog_acquisition_min_confidence: float = 70.0,
) -> AppleMusicImportService:
    cache_path = identity_cache_path or Path("cache/apple_music_identity.json")
    return AppleMusicImportService(
        applescript or AppleScriptClient(),
        IdentityCache(JsonCache(cache_path)),
        catalog=catalog,
        country_code=country_code,
        acquire_missing=acquire_missing,
        wait_for_manual_catalog_add=wait_for_manual_catalog_add,
        catalog_acquisition_min_confidence=catalog_acquisition_min_confidence,
    )


def build_default_registry(
    *,
    country: str = "us",
    catalog_cache=None,
    identity_cache_path: Path | None = None,
    acquire_missing: bool = True,
    wait_for_manual_catalog_add: bool = False,
    catalog_acquisition_min_confidence: float = 70.0,
) -> ProviderGatewayRegistry:
    registry = ProviderGatewayRegistry()
    registry.register(
        build_apple_music_gateway(
            country=country,
            cache=catalog_cache,
            identity_cache=IdentityCache(JsonCache(identity_cache_path or Path("cache/apple_music_identity.json"))),
            acquire_missing=acquire_missing,
            wait_for_manual_catalog_add=wait_for_manual_catalog_add,
            catalog_acquisition_min_confidence=catalog_acquisition_min_confidence,
        )
    )
    return registry
