from __future__ import annotations

from playlist_builder.canonical.contracts import CatalogSearchPort
from playlist_builder.canonical.models import CanonicalSearchRequest, CanonicalSearchResponse
from playlist_builder.integration.apple_music.itunes_client import ITunesSearchClient
from playlist_builder.integration.apple_music.mapper import search_response_from_hit


class AppleCatalogGateway(CatalogSearchPort):
    """Apple Music catalog search adapter implementing the canonical catalog port."""

    def __init__(self, client: ITunesSearchClient) -> None:
        self.client = client

    def search(self, request: CanonicalSearchRequest) -> CanonicalSearchResponse:
        hit, error = self.client.search_term(
            request.query,
            wanted_artist=request.wanted_artist,
            wanted_title=request.wanted_title,
            limit=request.limit,
        )
        if error and hit is None:
            return CanonicalSearchResponse(request=request, candidates=())
        return search_response_from_hit(
            request,
            hit,
            source="apple_music_catalog",
            reasons=(f"query:{request.query}",),
        )
