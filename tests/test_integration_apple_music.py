from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.canonical.models import CanonicalSearchRequest
from playlist_builder.catalog.apple_search import AppleCatalogSearch
from playlist_builder.core.models import TrackRef
from playlist_builder.infrastructure.cache.keys import catalog_entry_key
from playlist_builder.infrastructure.cache.store import JsonCache
from playlist_builder.integration.apple_music.catalog_gateway import AppleCatalogGateway
from playlist_builder.integration.apple_music.gateway import build_apple_music_gateway
from playlist_builder.integration.apple_music.itunes_client import ITunesSearchClient
from playlist_builder.integration.apple_music.mapper import catalog_match_from_track_search
from playlist_builder.integration.apple_music.models import AppleITunesSearchHit
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry


_ITUNES_RESULT = {
    "artistName": "Kygo",
    "trackName": "Firestone",
    "trackViewUrl": "https://music.apple.com/us/album/firestone/123",
    "collectionName": "Cloud Nine",
    "primaryGenreName": "Dance",
    "trackExplicitness": "notExplicit",
}


def _hit() -> AppleITunesSearchHit:
    return AppleITunesSearchHit(_ITUNES_RESULT)


def test_build_apple_music_gateway_exposes_catalog_port():
    gateway = build_apple_music_gateway(country="ch")

    assert gateway.provider_id == ProviderId.APPLE_MUSIC
    assert ProviderCapability.CATALOG_SEARCH in gateway.capabilities
    assert gateway.catalog is not None
    assert gateway.library is None
    assert gateway.delivery is None


def test_apple_catalog_gateway_maps_search_response():
    client = MagicMock()
    client.search_term.return_value = (_hit(), "")
    gateway = AppleCatalogGateway(client)
    request = CanonicalSearchRequest(
        query="Kygo Firestone",
        wanted_artist="Kygo",
        wanted_title="Firestone",
    )

    response = gateway.search(request)

    assert len(response.candidates) == 1
    assert response.candidates[0].track.title == "Firestone"
    assert response.candidates[0].track.artist.name == "Kygo"


def test_itunes_client_uses_namespaced_cache_keys(tmp_path: Path):
    cache = JsonCache(tmp_path / "catalog.json")
    client = ITunesSearchClient(country="us", cache=cache)
    track = TrackRef("Kygo", "Firestone")
    expected_key = catalog_entry_key(ProviderId.APPLE_MUSIC, "track", "us::kygo::firestone")

    with patch.object(client, "_search_once", return_value=_hit()):
        hit, error = client.search_track(track)

    assert error == ""
    assert hit is not None
    assert cache.get(expected_key) is not None


def test_itunes_client_reads_legacy_cache_keys(tmp_path: Path):
    cache = JsonCache(tmp_path / "catalog.json")
    legacy_key = "itunes::us::kygo::firestone"
    cache.set(
        legacy_key,
        {
            "matched_artist": "Kygo",
            "matched_title": "Firestone",
            "url": _ITUNES_RESULT["trackViewUrl"],
            "raw": _ITUNES_RESULT,
            "error": "",
        },
    )
    client = ITunesSearchClient(country="us", cache=cache)

    hit, error = client.search_track(TrackRef("Kygo", "Firestone"))

    assert error == ""
    assert hit is not None
    assert hit.artist_name == "Kygo"


def test_provider_gateway_registry_register_and_require():
    registry = ProviderGatewayRegistry()
    gateway = build_apple_music_gateway()

    registry.register(gateway)

    assert registry.get(ProviderId.APPLE_MUSIC) is gateway
    assert registry.list_provider_ids() == (ProviderId.APPLE_MUSIC,)
    assert registry.require(ProviderId.APPLE_MUSIC) is gateway


def test_apple_catalog_search_facade_preserves_legacy_surface(tmp_path: Path):
    cache = JsonCache(tmp_path / "catalog.json")
    search = AppleCatalogSearch(country="us", cache=cache)

    with patch.object(search._client, "_search_once", return_value=_hit()):
        match = search.search_track(TrackRef("Kygo", "Firestone"))

    assert match.matched_artist == "Kygo"
    assert match.matched_title == "Firestone"
    assert match.url == _ITUNES_RESULT["trackViewUrl"]


def test_catalog_match_mapper_handles_miss():
    track = TrackRef("Unknown", "Song")
    match = catalog_match_from_track_search(track, hit=None, error="not found")

    assert match.error == "not found"
    assert match.matched_artist == ""
