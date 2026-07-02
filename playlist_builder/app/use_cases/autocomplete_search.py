from __future__ import annotations

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.integration.apple_music.autocomplete_gateway import AppleAutocompleteGateway
from playlist_builder.integration.gateway.service import IntegrationGateway
from playlist_builder.ui.shared.autocomplete.genre_registry import search_genres
from playlist_builder.ui.shared.autocomplete.keyword_registry import search_keywords
from playlist_builder.ui.shared.dto.autocomplete import (
    AutocompleteEntityKind,
    AutocompleteRequest,
    AutocompleteResponse,
)


class AutocompleteSearchUseCase:
    """Provider-neutral autocomplete orchestration for the Smart Input bridge."""

    def __init__(
        self,
        integration_gateway: IntegrationGateway,
        *,
        apple_autocomplete: AppleAutocompleteGateway | None = None,
    ) -> None:
        self._integration_gateway = integration_gateway
        self._apple_autocomplete = apple_autocomplete or AppleAutocompleteGateway()

    def search(self, request: AutocompleteRequest) -> AutocompleteResponse:
        if request.entity_kind == AutocompleteEntityKind.GENRE:
            return AutocompleteResponse(suggestions=search_genres(request.query, limit=request.limit))

        if request.entity_kind == AutocompleteEntityKind.KEYWORD:
            return AutocompleteResponse(suggestions=search_keywords(request.query, limit=request.limit))

        if request.entity_kind == AutocompleteEntityKind.ARTIST:
            if request.provider_id != ProviderId.APPLE_MUSIC:
                return AutocompleteResponse()
            return self._apple_autocomplete.search_artists(request)

        if request.entity_kind == AutocompleteEntityKind.TRACK:
            if request.provider_id != ProviderId.APPLE_MUSIC:
                return AutocompleteResponse()
            artist_name = request.context.artist_name if request.context else ""
            return self._apple_autocomplete.search_tracks(request, artist_name=artist_name)

        return AutocompleteResponse()
