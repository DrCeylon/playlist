from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalArtist, CanonicalTrack, ProviderIdentity
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.infrastructure.cache import (
    IdentityCache,
    catalog_entry_key,
    identity_entry_key,
)
from playlist_builder.infrastructure.cache.store import JsonCache as InfrastructureJsonCache


def _track() -> CanonicalTrack:
    return CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone")


def test_identity_entry_key_is_namespaced():
    track = _track()
    assert identity_entry_key(ProviderId.APPLE_MUSIC, track.identity_key) == (
        "identity::apple_music::kygo::firestone"
    )


def test_catalog_entry_key_is_namespaced():
    assert catalog_entry_key(ProviderId.SPOTIFY, "search", "kygo::firestone") == (
        "catalog::spotify::search::kygo::firestone"
    )


def test_identity_cache_round_trip(tmp_path: Path):
    store = JsonCache(tmp_path / "identity.json")
    cache = IdentityCache(store)
    track = _track()
    resolved_at = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)

    identity = cache.put_identity(
        track,
        provider_id=ProviderId.APPLE_MUSIC,
        external_id="i.AbCdEf123",
        confidence=92.5,
        resolved_at=resolved_at,
    )

    cache.flush()
    reloaded = IdentityCache(JsonCache(tmp_path / "identity.json"))
    stored = reloaded.get(track, ProviderId.APPLE_MUSIC)

    assert stored == identity
    assert stored is not None
    assert stored.external_id == "i.AbCdEf123"
    assert stored.confidence == 92.5


def test_identity_cache_is_provider_scoped(tmp_path: Path):
    store = JsonCache(tmp_path / "identity.json")
    cache = IdentityCache(store)
    track = _track()

    cache.put_identity(track, provider_id=ProviderId.APPLE_MUSIC, external_id="apple-1", confidence=90)
    cache.put_identity(track, provider_id=ProviderId.SPOTIFY, external_id="spotify:track:1", confidence=88)

    assert cache.get(track, ProviderId.APPLE_MUSIC).external_id == "apple-1"
    assert cache.get(track, ProviderId.SPOTIFY).external_id == "spotify:track:1"


def test_identity_cache_invalidate_removes_entry(tmp_path: Path):
    store = JsonCache(tmp_path / "identity.json")
    cache = IdentityCache(store)
    track = _track()
    cache.put_identity(track, provider_id=ProviderId.APPLE_MUSIC, external_id="apple-1", confidence=90)

    assert cache.invalidate(track, ProviderId.APPLE_MUSIC) is True
    assert cache.get(track, ProviderId.APPLE_MUSIC) is None


def test_catalog_cache_facade_delegates_to_infrastructure_store(tmp_path: Path):
    path = tmp_path / "cache.json"
    facade = JsonCache(path)
    facade.set("key", {"ok": True})
    facade.flush()

    store = InfrastructureJsonCache(path)
    assert store.get("key") == {"ok": True}


def test_provider_identity_validation_rejects_invalid_confidence():
    with pytest.raises(ValueError, match="confidence"):
        ProviderIdentity(
            provider_id=ProviderId.APPLE_MUSIC,
            external_id="id",
            confidence=120.0,
            resolved_at=datetime.now(UTC),
        ).validate()
