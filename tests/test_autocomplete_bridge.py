from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from playlist_builder.app.use_cases.autocomplete_search import AutocompleteSearchUseCase
from playlist_builder.integration.apple_music.autocomplete_gateway import AppleAutocompleteGateway
from playlist_builder.integration.apple_music.models import AppleITunesSearchHit
from playlist_builder.ui.bridge.commands import BridgeCommand, autocomplete_request_from_dict
from playlist_builder.ui.bridge.json_rpc import JsonRpcEngineBridge
from playlist_builder.ui.shared.autocomplete.genre_registry import search_genres
from playlist_builder.ui.shared.autocomplete.keyword_registry import search_keywords
from playlist_builder.ui.shared.dto.autocomplete import (
    AutocompleteEntityKind,
    AutocompleteRequest,
    AutocompleteResponse,
)
from playlist_builder.canonical.enums import ProviderId


class FakeAutocompleteBackend:
    def autocomplete_search(self, params: dict) -> object:
        from playlist_builder.ui.bridge.commands import AutocompleteSearchResult

        request = autocomplete_request_from_dict(params)
        if request.entity_kind == AutocompleteEntityKind.ARTIST:
            from playlist_builder.ui.shared.dto.autocomplete import ArtistSuggestion

            return AutocompleteSearchResult(
                response=AutocompleteResponse(
                    suggestions=(
                        ArtistSuggestion(id="muse", display_name="Muse"),
                    )
                )
            )
        return AutocompleteSearchResult(response=AutocompleteResponse())


def test_bridge_command_autocomplete_raw_value() -> None:
    assert BridgeCommand.AUTOCOMPLETE_SEARCH.value == "autocomplete_search"


def test_autocomplete_request_from_dict_parses_context() -> None:
    request = autocomplete_request_from_dict(
        {
            "provider_id": "apple_music",
            "entity_kind": "track",
            "query": "fire",
            "limit": 5,
            "context": {"artist_name": "Kygo"},
        }
    )
    assert request.entity_kind == AutocompleteEntityKind.TRACK
    assert request.context is not None
    assert request.context.artist_name == "Kygo"


def test_json_rpc_autocomplete_search() -> None:
    bridge = JsonRpcEngineBridge(backend=FakeAutocompleteBackend())
    messages = bridge.handle(
        {
            "id": "ac-1",
            "command": "autocomplete_search",
            "params": {
                "provider_id": "apple_music",
                "entity_kind": "artist",
                "query": "mu",
            },
        }
    )
    response = messages[-1]
    assert response["ok"] is True
    assert response["result"]["suggestions"][0]["display_name"] == "Muse"


def test_genre_registry_synonym_mapping() -> None:
    results = search_genres("Hip Hop")
    assert any(item.display_name == "Hip-Hop" for item in results)


def test_keyword_registry_suggestions() -> None:
    results = search_keywords("sum")
    assert any(item.label == "Summer" for item in results)


def test_apple_autocomplete_gateway_maps_artists(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    client.search_artists.return_value = (
        [AppleITunesSearchHit({"artistName": "Muse", "artistId": 123})],
        "",
    )
    gateway = AppleAutocompleteGateway(client=client)
    response = gateway.search_artists(
        AutocompleteRequest(
            provider_id=ProviderId.APPLE_MUSIC,
            entity_kind=AutocompleteEntityKind.ARTIST,
            query="muse",
        )
    )
    assert response.suggestions[0].display_name == "Muse"


def test_apple_autocomplete_gateway_filters_tracks_by_artist() -> None:
    client = MagicMock()
    client.search_tracks.return_value = (
        [
            AppleITunesSearchHit({"artistName": "Kygo", "trackName": "Firestone", "trackId": 1}),
            AppleITunesSearchHit({"artistName": "Muse", "trackName": "Fire and Fury", "trackId": 2}),
        ],
        "",
    )
    gateway = AppleAutocompleteGateway(client=client)
    response = gateway.search_tracks(
        AutocompleteRequest(
            provider_id=ProviderId.APPLE_MUSIC,
            entity_kind=AutocompleteEntityKind.TRACK,
            query="fire",
        ),
        artist_name="Kygo",
    )
    assert len(response.suggestions) == 1
    assert response.suggestions[0].title == "Firestone"
    assert response.suggestions[0].artist_name == "Kygo"


def test_autocomplete_use_case_genre_is_local() -> None:
    use_case = AutocompleteSearchUseCase(integration_gateway=MagicMock())
    response = use_case.search(
        AutocompleteRequest(
            provider_id=ProviderId.APPLE_MUSIC,
            entity_kind=AutocompleteEntityKind.GENRE,
            query="metal",
        )
    )
    assert any(item.display_name == "Heavy Metal" for item in response.suggestions)
