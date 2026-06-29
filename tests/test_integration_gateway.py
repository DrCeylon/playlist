from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from playlist_builder.canonical.enums import ImportStatus, ProviderId
from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalImportReport,
    CanonicalImportResult,
    CanonicalPlaylist,
    CanonicalPlaylistSection,
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
