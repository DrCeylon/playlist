from __future__ import annotations

# Host extension API version. Bump minor for additive manifest fields;
# bump major for breaking extension contracts.
EXTENSION_API_VERSION = "1.0.0"

# Bridge JSON-RPC command surface version (Swift + Python BridgeCommand enum).
BRIDGE_API_VERSION = "1.0.0"


def is_extension_api_compatible(manifest_version: str) -> bool:
    """Return True when a plugin manifest can load against this host."""
    host_parts = EXTENSION_API_VERSION.split(".")
    manifest_parts = str(manifest_version).strip().split(".")
    if len(host_parts) < 1 or len(manifest_parts) < 1:
        return False
    return host_parts[0] == manifest_parts[0]
