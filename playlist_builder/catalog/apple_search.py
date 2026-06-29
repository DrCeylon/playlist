"""Backward-compatible Apple catalog search facade.

New code should use :mod:`playlist_builder.integration.apple_music`.
"""

from __future__ import annotations

from playlist_builder.catalog.rate_limiter import RateLimiter
from playlist_builder.catalog.retry_policy import RetryPolicy
from playlist_builder.core.models import CatalogMatch, TrackRef
from playlist_builder.infrastructure.cache.store import JsonCache
from playlist_builder.integration.apple_music.gateway import build_apple_music_gateway
from playlist_builder.integration.apple_music.itunes_client import ITunesSearchClient
from playlist_builder.integration.apple_music.mapper import catalog_match_from_term_search, catalog_match_from_track_search


class AppleCatalogSearch:
    """Facade preserving the legacy check_catalog / discovery wiring surface."""

    def __init__(
        self,
        country: str = "us",
        cache: JsonCache | None = None,
        rate_limiter: RateLimiter | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.country = country
        self.rate_limiter = rate_limiter or RateLimiter(minimum_interval_seconds=0.5)
        self.retry_policy = retry_policy or RetryPolicy()
        self._gateway = build_apple_music_gateway(
            country=country,
            cache=cache,
            rate_limiter=self.rate_limiter,
            retry_policy=self.retry_policy,
        )
        self._client: ITunesSearchClient = self._gateway.catalog.client

    @property
    def cache(self) -> JsonCache | None:
        return self._client.cache

    def search_track(self, track: TrackRef, limit: int = 5) -> CatalogMatch:
        hit, error = self._client.search_track(track, limit=limit)
        return catalog_match_from_track_search(track, hit=hit, error=error)

    def search_term(
        self,
        term: str,
        *,
        wanted_artist: str = "",
        wanted_title: str = "",
        limit: int = 5,
    ) -> CatalogMatch:
        hit, error = self._client.search_term(
            term,
            wanted_artist=wanted_artist,
            wanted_title=wanted_title,
            limit=limit,
        )
        return catalog_match_from_term_search(
            wanted_artist=wanted_artist,
            wanted_title=wanted_title,
            term=term,
            hit=hit,
            error=error,
        )
