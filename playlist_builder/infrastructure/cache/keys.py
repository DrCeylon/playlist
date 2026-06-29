from __future__ import annotations

from playlist_builder.canonical.enums import ProviderId


def identity_entry_key(provider_id: ProviderId, track_identity_key: str) -> str:
    """Build a namespaced cache key for canonical track → provider identity."""

    return f"identity::{provider_id.value}::{track_identity_key}"


def catalog_entry_key(provider_id: ProviderId, namespace: str, key: str) -> str:
    """Build a namespaced cache key for provider catalog lookups."""

    return f"catalog::{provider_id.value}::{namespace}::{key}"
