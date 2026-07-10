from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playlist_builder.platform.api_version import is_extension_api_compatible
from playlist_builder.platform.extension_points import ACTIVE_EXTENSION_POINTS, ExtensionPointId


@dataclass(frozen=True, slots=True)
class ExtensionManifest:
    """In-process extension manifest (monorepo or future packaged plugin)."""

    id: str
    extension_point: ExtensionPointId
    api_version: str
    entry: str
    display_name: str = ""
    permissions: frozenset[str] = frozenset()


class ExtensionManifestError(ValueError):
    """Invalid or incompatible extension manifest."""


def parse_extension_manifest(raw: dict[str, Any]) -> ExtensionManifest:
    """Parse and validate a manifest dict. Does not import or execute entry."""
    if not isinstance(raw, dict):
        raise ExtensionManifestError("manifest must be a JSON object")

    extension_id = str(raw.get("id", "")).strip()
    if not extension_id:
        raise ExtensionManifestError("manifest.id is required")

    point_raw = str(raw.get("extension_point", "")).strip()
    try:
        extension_point = ExtensionPointId(point_raw)
    except ValueError as exc:
        raise ExtensionManifestError(f"unknown extension_point: {point_raw!r}") from exc

    api_version = str(raw.get("api_version", "")).strip()
    if not api_version:
        raise ExtensionManifestError("manifest.api_version is required")
    if not is_extension_api_compatible(api_version):
        raise ExtensionManifestError(
            f"manifest api_version {api_version!r} is incompatible with host extension API"
        )

    entry = str(raw.get("entry", "")).strip()
    if not entry:
        raise ExtensionManifestError("manifest.entry is required (module:callable or theme path)")

    display_name = str(raw.get("display_name", "")).strip()
    permissions_raw = raw.get("permissions", [])
    permissions: set[str] = set()
    if permissions_raw:
        if not isinstance(permissions_raw, list):
            raise ExtensionManifestError("manifest.permissions must be a list of strings")
        for item in permissions_raw:
            if not isinstance(item, str) or not item.strip():
                raise ExtensionManifestError("manifest.permissions entries must be non-empty strings")
            permissions.add(item.strip())

    return ExtensionManifest(
        id=extension_id,
        extension_point=extension_point,
        api_version=api_version,
        entry=entry,
        display_name=display_name,
        permissions=frozenset(permissions),
    )


def extension_point_is_active(extension_point: ExtensionPointId) -> bool:
    return extension_point in ACTIVE_EXTENSION_POINTS
