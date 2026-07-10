"""Tests for multi-provider readiness improvements."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from playlist_builder.app.bridge_runtime.provider_platform import provider_options_from_registry
from playlist_builder.app.factory import build_app_context, get_provider_import_port
from playlist_builder.app.settings import AppSettings
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.canonical.provider_ids import parse_provider_id, provider_display_name
from playlist_builder.integration.apple_music.provider_import_port import AppleMusicProviderImportPort
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry


def test_parse_provider_id_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown provider_id"):
        parse_provider_id("spotify_streaming")


def test_parse_provider_id_defaults_when_missing():
    assert parse_provider_id(None, default=ProviderId.APPLE_MUSIC) == ProviderId.APPLE_MUSIC


def test_provider_display_names_cover_planned_providers():
    for provider_id in (
        ProviderId.SPOTIFY,
        ProviderId.PLEX,
        ProviderId.LOCAL_FILES,
        ProviderId.NAVIDROME,
    ):
        assert provider_display_name(provider_id)


def test_get_provider_import_port_uses_gateway_import_port_not_provider_if():
    context = build_app_context(AppSettings())
    port = get_provider_import_port(context, ProviderId.APPLE_MUSIC)
    assert isinstance(port, AppleMusicProviderImportPort)

    factory_source = Path(__file__).resolve().parents[1] / "playlist_builder" / "app" / "factory.py"
    tree = ast.parse(factory_source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comparator in node.comparators:
                if isinstance(comparator, ast.Attribute) and comparator.attr == "APPLE_MUSIC":
                    pytest.fail("factory.get_provider_import_port must not branch on ProviderId.APPLE_MUSIC")


def test_provider_options_from_registry_marks_apple_unavailable_off_macos(monkeypatch):
    if sys.platform == "darwin":
        pytest.skip("macOS reports Apple Music as available")

    context = build_app_context(AppSettings())
    options = provider_options_from_registry(context.registry)
    apple = next(item for item in options if item.provider_id == ProviderId.APPLE_MUSIC)
    assert apple.is_available is False
    assert apple.unavailable_reason


def test_provider_options_from_registry_includes_youtube_when_registered():
    context = build_app_context(AppSettings())
    options = provider_options_from_registry(context.registry)
    youtube = next(item for item in options if item.provider_id == ProviderId.YOUTUBE_MUSIC)
    assert youtube.is_experimental is True
    assert ProviderCapability.AUTHENTICATION in youtube.capabilities


def test_provider_platform_has_no_provider_specific_if_branches():
    source = Path(__file__).resolve().parents[1] / "playlist_builder" / "app" / "bridge_runtime" / "provider_platform.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comparator in node.comparators:
                if isinstance(comparator, ast.Attribute) and comparator.attr in {
                    "APPLE_MUSIC",
                    "YOUTUBE_MUSIC",
                }:
                    pytest.fail("provider_platform must not branch on specific provider ids")


def test_registry_gateway_can_expose_import_port_via_duck_typing():
    registry = ProviderGatewayRegistry()
    gateway = MagicMock()
    gateway.provider_id = ProviderId.SPOTIFY
    gateway.import_port = MagicMock()
    registry.register(gateway)
    port = getattr(registry.require(ProviderId.SPOTIFY), "import_port", None)
    assert port is not None
