"""Plugin platform foundation tests."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.platform.api_version import EXTENSION_API_VERSION, is_extension_api_compatible
from playlist_builder.platform.extension_points import ACTIVE_EXTENSION_POINTS, ExtensionPointId
from playlist_builder.platform.manifest import ExtensionManifestError, parse_extension_manifest


def test_extension_api_version_is_semver_shape():
    parts = EXTENSION_API_VERSION.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_api_compatibility_major_match():
    assert is_extension_api_compatible(EXTENSION_API_VERSION)
    assert is_extension_api_compatible("1.2.3")
    assert not is_extension_api_compatible("2.0.0")


def test_parse_valid_music_provider_manifest():
    manifest = parse_extension_manifest(
        {
            "id": "resonance.provider.demo",
            "extension_point": "music_provider",
            "api_version": EXTENSION_API_VERSION,
            "entry": "playlist_builder.integration.demo.gateway:build",
            "permissions": ["network", "provider.auth"],
        }
    )
    assert manifest.extension_point == ExtensionPointId.MUSIC_PROVIDER
    assert manifest.permissions == frozenset({"network", "provider.auth"})


def test_parse_rejects_unknown_extension_point():
    with pytest.raises(ExtensionManifestError, match="unknown extension_point"):
        parse_extension_manifest(
            {
                "id": "bad",
                "extension_point": "not_a_real_point",
                "api_version": EXTENSION_API_VERSION,
                "entry": "mod:fn",
            }
        )


def test_parse_rejects_incompatible_api_version():
    with pytest.raises(ExtensionManifestError, match="incompatible"):
        parse_extension_manifest(
            {
                "id": "future",
                "extension_point": "music_provider",
                "api_version": "99.0.0",
                "entry": "mod:fn",
            }
        )


def test_provider_registry_declares_extension_point():
    assert ProviderGatewayRegistry.extension_point_id == ExtensionPointId.MUSIC_PROVIDER


def test_active_extension_points_include_music_provider():
    assert ExtensionPointId.MUSIC_PROVIDER in ACTIVE_EXTENSION_POINTS


def test_platform_package_does_not_import_integration():
    platform_dir = Path(__file__).resolve().parents[1] / "playlist_builder" / "platform"
    offenders: list[str] = []
    for path in platform_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("playlist_builder.integration"):
                        offenders.append(f"{path.name} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("playlist_builder.integration"):
                    offenders.append(f"{path.name} imports from {node.module}")
    assert offenders == []


def test_extension_manifest_schema_file_exists():
    schema = Path(__file__).resolve().parents[1] / "schemas" / "resonance-extension-manifest.schema.json"
    assert schema.is_file()
    assert "music_provider" in schema.read_text(encoding="utf-8")


def test_diagnostics_includes_extension_api_version():
    from playlist_builder.app.bridge_runtime.diagnostics_snapshot import build_diagnostics_snapshot
    from playlist_builder.app.factory import build_app_context

    context = build_app_context()
    summary, _events = build_diagnostics_snapshot(context, providers=())
    assert summary["extension_api_version"] == EXTENSION_API_VERSION
    assert "extension_points" in summary
    assert summary["bridge_api_version"]
