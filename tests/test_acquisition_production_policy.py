from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock

from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
from playlist_builder.integration.apple_music.acquisition_policy import (
    ENABLE_PLAY_DUPLICATE_ACQUISITION_DEFAULT,
    PRODUCTION_ADDED_LIBRARY_PROBE_ATTEMPTS,
)
from playlist_builder.integration.apple_music.library_acquisition import (
    AppleMusicAcquisitionStatus,
    AppleMusicLibraryAcquisition,
)
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.integration.apple_music.resolver import AppleMusicResolutionStatus, AppleMusicResolver


def _track() -> CanonicalTrack:
    return CanonicalTrack(artist=CanonicalArtist(name="Dwayne Johnson"), title="You're Welcome")


def _catalog_candidate(track: CanonicalTrack | None = None) -> CanonicalCandidate:
    track = track or _track()
    return CanonicalCandidate(
        track=track,
        source="itunes_catalog",
        provider_hints=(
            "https://music.apple.com/us/song/youre-welcome/6779424544",
            "itunes_track_id:6779424544",
        ),
        raw_confidence=100.0,
        reasons=("test",),
    )


def test_play_duplicate_disabled_by_default():
    assert ENABLE_PLAY_DUPLICATE_ACQUISITION_DEFAULT is False


def test_production_acquisition_skips_s2_and_opens_for_manual():
    applescript = MagicMock()
    applescript.try_add_catalog_url.return_value = ""
    acquisition = AppleMusicLibraryAcquisition(applescript)

    outcome = acquisition.acquire_from_catalog_candidate(_catalog_candidate())

    assert outcome.status == AppleMusicAcquisitionStatus.OPENED
    assert applescript.try_add_catalog_url.called
    applescript.open_catalog_url_for_manual.assert_called_once()
    applescript.acquire_song_from_url.assert_not_called()


def test_production_acquisition_quick_add_returns_added():
    applescript = MagicMock()
    applescript.try_add_catalog_url.return_value = "5A9F4F4AF88E2299"
    acquisition = AppleMusicLibraryAcquisition(applescript)

    outcome = acquisition.acquire_from_catalog_candidate(_catalog_candidate())

    assert outcome.status == AppleMusicAcquisitionStatus.ADDED
    assert outcome.detail == "5A9F4F4AF88E2299"
    applescript.acquire_song_from_url.assert_not_called()


def test_legacy_experimental_still_uses_s2():
    applescript = MagicMock()
    applescript.acquire_song_from_url.return_value = ("opened", "legacy")
    acquisition = AppleMusicLibraryAcquisition(
        applescript,
        acquisition_mode="legacy_experimental",
    )

    acquisition.acquire_from_catalog_candidate(_catalog_candidate())

    applescript.acquire_song_from_url.assert_called_once()
    applescript.try_add_catalog_url.assert_not_called()


def test_resolver_cache_hit_skips_acquisition(tmp_path: Path):
    from datetime import UTC, datetime

    from playlist_builder.canonical.enums import ProviderId

    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    track = _track()
    identity_cache.put_identity(
        track,
        provider_id=ProviderId.APPLE_MUSIC,
        external_id="CACHED-PID",
        confidence=95.0,
        resolved_at=datetime(2026, 7, 5, tzinfo=UTC),
    )

    applescript = MagicMock()
    catalog = MagicMock()
    resolver = AppleMusicResolver(
        applescript,
        identity_cache,
        catalog=catalog,
        acquire_missing=True,
        wait_for_manual_catalog_add=True,
    )

    outcome = resolver.resolve(track)

    assert outcome.status == AppleMusicResolutionStatus.RESOLVED
    assert outcome.persistent_id == "CACHED-PID"
    assert outcome.cache_hit is True
    catalog.search.assert_not_called()
    applescript.try_add_catalog_url.assert_not_called()
    applescript.acquire_song_from_url.assert_not_called()


def test_resolver_triggers_manual_without_s2_delay(tmp_path: Path, monkeypatch):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = [
        [[]],
        [[AppleMusicTrack(persistent_id="PID-MANUAL", artist="Dwayne Johnson", title="You're Welcome", query="You're Welcome")]],
    ]
    applescript.try_add_catalog_url.return_value = ""
    sleeps: list[float] = []
    monkeypatch.setattr(
        "playlist_builder.integration.apple_music.resolver.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    hook_calls: list[tuple[str, str]] = []

    def hook(track, catalog_candidate, detail) -> None:
        hook_calls.append((track.title, detail))

    catalog = MagicMock()
    catalog.search.return_value = CanonicalSearchResponse(
        request=CanonicalSearchRequest(query="Dwayne Johnson You're Welcome"),
        candidates=(_catalog_candidate(),),
    )

    resolver = AppleMusicResolver(
        applescript,
        identity_cache,
        catalog=catalog,
        acquire_missing=True,
        wait_for_manual_catalog_add=True,
        manual_acquisition_hook=hook,
    )

    started = time.monotonic()
    outcome = resolver.resolve(_track())
    elapsed = time.monotonic() - started

    assert outcome.status == AppleMusicResolutionStatus.RESOLVED
    assert outcome.persistent_id == "PID-MANUAL"
    assert hook_calls
    applescript.acquire_song_from_url.assert_not_called()
    assert elapsed < 2.0
    assert not sleeps
