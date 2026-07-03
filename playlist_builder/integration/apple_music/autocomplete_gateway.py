from __future__ import annotations

import re
import unicodedata

from playlist_builder.integration.apple_music.itunes_client import ITunesSearchClient
from playlist_builder.integration.apple_music.mapper import (
    artist_suggestion_from_itunes_hit,
    track_suggestion_from_itunes_hit,
)
from playlist_builder.integration.apple_music.models import AppleITunesSearchHit
from playlist_builder.ui.shared.dto.autocomplete import AutocompleteRequest, AutocompleteResponse
from playlist_builder.scoring.match_engine import score_text_match


def _normalize_identity(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


class AppleAutocompleteGateway:
    """Apple Music autocomplete adapter for the Smart Input framework."""

    def __init__(self, client: ITunesSearchClient | None = None) -> None:
        self.client = client or ITunesSearchClient()

    def search_artists(self, request: AutocompleteRequest) -> AutocompleteResponse:
        hits, error = self.client.search_artists(request.query, limit=request.limit)
        if error and not hits:
            return AutocompleteResponse()
        suggestions = tuple(artist_suggestion_from_itunes_hit(hit) for hit in hits)
        return AutocompleteResponse(suggestions=suggestions)

    def search_tracks(self, request: AutocompleteRequest, *, artist_name: str = "") -> AutocompleteResponse:
        hits, error = self.client.search_tracks(
            request.query,
            limit=request.limit,
            wanted_artist=artist_name,
        )
        if error and not hits:
            return AutocompleteResponse()

        if artist_name.strip():
            ranked = sorted(
                hits,
                key=lambda hit: score_text_match(artist_name, request.query, hit.artist_name, hit.track_name),
                reverse=True,
            )
        else:
            ranked = hits

        suggestions = tuple(track_suggestion_from_itunes_hit(hit) for hit in ranked[: request.limit])
        return AutocompleteResponse(suggestions=suggestions)
