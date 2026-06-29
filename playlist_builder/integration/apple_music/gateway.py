from __future__ import annotations

from playlist_builder.canonical.contracts import CatalogSearchPort, ProviderGateway
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.apple_music.catalog_gateway import AppleCatalogGateway
from playlist_builder.integration.apple_music.itunes_client import ITunesSearchClient


class AppleMusicProviderGateway(ProviderGateway):
    """Apple Music provider gateway exposing catalog search capabilities."""

    def __init__(self, catalog: AppleCatalogGateway) -> None:
        self._catalog = catalog

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.APPLE_MUSIC

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        return frozenset({ProviderCapability.CATALOG_SEARCH})

    @property
    def catalog(self) -> CatalogSearchPort:
        return self._catalog

    @property
    def library(self) -> None:
        return None

    @property
    def delivery(self) -> None:
        return None


def build_apple_music_gateway(
    *,
    country: str = "us",
    cache=None,
    rate_limiter=None,
    retry_policy=None,
) -> AppleMusicProviderGateway:
    client = ITunesSearchClient(
        country=country,
        cache=cache,
        rate_limiter=rate_limiter,
        retry_policy=retry_policy,
    )
    return AppleMusicProviderGateway(AppleCatalogGateway(client))
