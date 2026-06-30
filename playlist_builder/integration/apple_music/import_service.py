from __future__ import annotations

from playlist_builder.canonical.contracts import CatalogSearchPort
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalPlaylist, CanonicalTrack
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.delivery import AppleMusicDelivery
from playlist_builder.integration.apple_music.resolver import AppleMusicResolver


def flatten_playlist_rows(playlist: CanonicalPlaylist) -> list[tuple[CanonicalTrack, str]]:
    from playlist_builder.canonical.models import CanonicalTrack

    rows: list[tuple[CanonicalTrack, str]] = []
    for section in playlist.sections:
        for track in section.tracks:
            rows.append((track, section.name))
    return rows


class AppleMusicImportService:
    """Orchestrates identity-cache resolution and Apple Music playlist delivery."""

    def __init__(
        self,
        applescript: AppleScriptClient,
        identity_cache: IdentityCache,
        *,
        catalog: CatalogSearchPort | None = None,
        country_code: str = "us",
        acquire_missing: bool = False,
        wait_for_manual_catalog_add: bool = False,
        catalog_acquisition_min_confidence: float = 70.0,
    ) -> None:
        self._applescript = applescript
        self._identity_cache = identity_cache
        self._resolver = AppleMusicResolver(
            applescript,
            identity_cache,
            catalog=catalog,
            country_code=country_code,
            acquire_missing=acquire_missing,
            wait_for_manual_catalog_add=wait_for_manual_catalog_add,
            catalog_acquisition_min_confidence=catalog_acquisition_min_confidence,
        )
        self._delivery = AppleMusicDelivery(applescript)

    @property
    def applescript(self) -> AppleScriptClient:
        return self._applescript

    @property
    def resolver(self) -> AppleMusicResolver:
        return self._resolver

    @property
    def delivery(self) -> AppleMusicDelivery:
        return self._delivery

    @property
    def identity_cache(self) -> IdentityCache:
        return self._identity_cache

    def import_playlist(
        self,
        playlist: CanonicalPlaylist,
        *,
        sync: bool = True,
        existing_keys: set[str] | None = None,
        allow_duplicates: bool = False,
    ) -> CanonicalImportReport:
        rows = flatten_playlist_rows(playlist)
        outcomes = self._resolver.resolve_batch(rows)
        self._delivery.ensure_playlist(playlist.name)

        if sync:
            return self._delivery.sync_playlist(playlist, outcomes)

        return self._delivery.import_incremental(
            playlist,
            outcomes,
            existing_keys=existing_keys,
            allow_duplicates=allow_duplicates,
        )
