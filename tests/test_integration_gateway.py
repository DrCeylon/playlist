from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from playlist_builder.canonical.enums import ImportStatus, ProviderId
from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalImportReport,
    CanonicalImportResult,
    CanonicalPlaylist,
    CanonicalPlaylistSection,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.integration.apple_music.gateway import build_default_registry
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.integration.gateway.service import IntegrationGateway


def _playlist() -> CanonicalPlaylist:
    return CanonicalPlaylist(
        name="E2E Test",
        sections=(
            CanonicalPlaylistSection(
                name="Playlist",
                tracks=(CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone"),),
            ),
        ),
    )


def test_default_registry_registers_apple_music(tmp_path: Path):
    registry = build_default_registry(identity_cache_path=tmp_path / "identity.json")

    gateway = registry.require(ProviderId.APPLE_MUSIC)

    assert ProviderId.APPLE_MUSIC in registry.list_provider_ids()
    assert gateway.delivery is not None


def test_integration_gateway_routes_import_playlist(tmp_path: Path):
    registry = build_default_registry(identity_cache_path=tmp_path / "identity.json")
    gateway = IntegrationGateway(registry)
    apple_gateway = registry.require(ProviderId.APPLE_MUSIC)
    expected = CanonicalImportReport(
        playlist_name="E2E Test",
        results=(
            CanonicalImportResult(
                track=_playlist().tracks[0],
                status=ImportStatus.ADDED,
                section_name="Playlist",
            ),
        ),
    )
    apple_gateway.import_service.import_playlist = MagicMock(return_value=expected)

    report = gateway.import_playlist(_playlist(), sync=True)

    assert report == expected


def test_integration_gateway_routes_incremental_import(tmp_path: Path):
    registry = build_default_registry(identity_cache_path=tmp_path / "identity.json")
    gateway = IntegrationGateway(registry)
    apple_gateway = registry.require(ProviderId.APPLE_MUSIC)
    expected = CanonicalImportReport(playlist_name="E2E Test", results=())
    apple_gateway.import_service.import_playlist = MagicMock(return_value=expected)

    report = gateway.import_playlist(
        _playlist(),
        sync=False,
        existing_keys={"kygo::firestone"},
        allow_duplicates=False,
    )

    apple_gateway.import_service.import_playlist.assert_called_once_with(
        _playlist(),
        sync=False,
        existing_keys={"kygo::firestone"},
        allow_duplicates=False,
    )
    assert report == expected


def test_integration_gateway_prepare_incremental_import(tmp_path: Path):
    registry = build_default_registry(identity_cache_path=tmp_path / "identity.json")
    gateway = IntegrationGateway(registry)
    apple_gateway = registry.require(ProviderId.APPLE_MUSIC)
    applescript = apple_gateway.import_service.applescript
    applescript.ensure_running = MagicMock()
    applescript.ensure_playlist = MagicMock()
    applescript.load_playlist_keys = MagicMock(return_value={"kygo::firestone"})

    context = gateway.prepare_incremental_import("E2E Test")

    applescript.ensure_running.assert_called_once()
    applescript.ensure_playlist.assert_called_once_with("E2E Test")
    assert context.existing_keys == {"kygo::firestone"}


def test_integration_gateway_search_catalog(tmp_path: Path):
    registry = build_default_registry(identity_cache_path=tmp_path / "identity.json")
    gateway = IntegrationGateway(registry)
    apple_gateway = registry.require(ProviderId.APPLE_MUSIC)
    request = CanonicalSearchRequest(query="Kygo Firestone", wanted_artist="Kygo", wanted_title="Firestone")
    expected = CanonicalSearchResponse(
        request=request,
        candidates=(
            CanonicalCandidate(
                track=CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone"),
                source="itunes",
                provider_hints=("https://music.apple.com/track/1",),
                raw_confidence=95.0,
            ),
        ),
    )
    apple_gateway.catalog.search = MagicMock(return_value=expected)

    response = gateway.search_catalog(request)

    assert response == expected


def test_integration_gateway_flush_caches(tmp_path: Path):
    registry = build_default_registry(
        identity_cache_path=tmp_path / "identity.json",
        catalog_cache=MagicMock(),
    )
    gateway = IntegrationGateway(registry)
    apple_gateway = registry.require(ProviderId.APPLE_MUSIC)
    apple_gateway.import_service.identity_cache.flush = MagicMock()
    catalog_cache = apple_gateway.catalog.client.cache
    catalog_cache.flush = MagicMock()

    gateway.flush_caches(flush_catalog_cache=True)

    apple_gateway.import_service.identity_cache.flush.assert_called_once()
    catalog_cache.flush.assert_called_once()


def test_integration_gateway_requires_delivery_capability():
    registry = ProviderGatewayRegistry()
    provider = MagicMock()
    provider.capabilities = frozenset()
    provider.delivery = None
    provider.provider_id = ProviderId.APPLE_MUSIC
    registry.register(provider)
    gateway = IntegrationGateway(registry)

    with pytest.raises(ValueError, match="playlist delivery"):
        gateway.import_playlist(_playlist())
