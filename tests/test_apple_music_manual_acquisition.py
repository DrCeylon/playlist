from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
from playlist_builder.integration.apple_music.library_acquisition import (
    AppleMusicAcquisitionStatus,
    AppleMusicLibraryAcquisition,
)
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.integration.apple_music.resolver import AppleMusicResolutionStatus, AppleMusicResolver


class FakeCatalog:
    def __init__(self, candidate: CanonicalCandidate | None) -> None:
        self._candidate = candidate

    def search(self, request: CanonicalSearchRequest) -> CanonicalSearchResponse:
        return CanonicalSearchResponse(
            request=request,
            candidates=tuple([self._candidate] if self._candidate else []),
        )


def _track() -> CanonicalTrack:
    return CanonicalTrack(artist=CanonicalArtist(name="Daft Punk"), title="One More Time")


def _catalog_candidate(track: CanonicalTrack) -> CanonicalCandidate:
    return CanonicalCandidate(
        track=track,
        source="itunes_catalog",
        provider_hints=("music://catalog/one-more-time",),
        raw_confidence=100.0,
        reasons=("test",),
    )


def test_library_acquisition_exposes_opened_status_without_losing_legacy_unpacking():
    applescript = MagicMock()
    applescript.acquire_song_from_url.return_value = ("opened", "URL ouverte")
    acquisition = AppleMusicLibraryAcquisition(applescript, settle_delay_seconds=0)

    outcome = acquisition.acquire_from_catalog_candidate(_catalog_candidate(_track()))
    legacy_added, legacy_detail = outcome

    assert outcome.status == AppleMusicAcquisitionStatus.OPENED
    assert outcome.opened is True
    assert legacy_added is False
    assert legacy_detail == "URL ouverte"


def test_resolver_retries_after_manual_acquisition_confirmation(tmp_path: Path, monkeypatch):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = [
        [[]],
        [[AppleMusicTrack(persistent_id="PID-ONE", artist="Daft Punk", title="One More Time", query="One More Time")]],
    ]
    applescript.acquire_song_from_url.return_value = ("opened", "URL ouverte dans Music")
    monkeypatch.setattr("builtins.input", lambda: "")

    resolver = AppleMusicResolver(
        applescript,
        identity_cache,
        catalog=FakeCatalog(_catalog_candidate(_track())),
        acquire_missing=True,
        wait_for_manual_catalog_add=True,
    )

    outcome = resolver.resolve(_track())

    assert outcome.status == AppleMusicResolutionStatus.RESOLVED
    assert outcome.persistent_id == "PID-ONE"
    assert outcome.catalog_acquired is True
    assert identity_cache.get(_track(), ProviderId.APPLE_MUSIC) is not None
    assert applescript.collect_candidates_batch.call_count == 2


def test_resolver_can_open_catalog_without_waiting(tmp_path: Path):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = [[[]], [[]]]
    applescript.acquire_song_from_url.return_value = ("opened", "URL ouverte dans Music")

    resolver = AppleMusicResolver(
        applescript,
        identity_cache,
        catalog=FakeCatalog(_catalog_candidate(_track())),
        acquire_missing=True,
        wait_for_manual_catalog_add=False,
    )

    outcome = resolver.resolve(_track())

    assert outcome.status == AppleMusicResolutionStatus.NOT_FOUND
    assert "Morceau toujours absent" in outcome.error
