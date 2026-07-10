"""Resonance extension platform — versioned contracts and extension point IDs.

This package defines stable identifiers for in-process extensions today.
It does not load third-party code; see docs/PLUGIN_PLATFORM_AUDIT.md.
"""

from playlist_builder.platform.api_version import (
    BRIDGE_API_VERSION,
    EXTENSION_API_VERSION,
    is_extension_api_compatible,
)
from playlist_builder.platform.extension_points import ExtensionPointId
from playlist_builder.platform.manifest import ExtensionManifest, parse_extension_manifest

__all__ = [
    "BRIDGE_API_VERSION",
    "EXTENSION_API_VERSION",
    "ExtensionManifest",
    "ExtensionPointId",
    "is_extension_api_compatible",
    "parse_extension_manifest",
]
