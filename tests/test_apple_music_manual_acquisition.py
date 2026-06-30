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
    acquisition = AppleMusicLibraryAcquisition(
        applescript,
        settle_delay_seconds=0,
        play_delay_seconds=0,
    )

    outcome = acquisition.acquire_from_catalog_candidate(_catalog_candidate(_track()))
    legacy_added, legacy_detail = outcome

    assert outcome.status == AppleMusicAcquisitionStatus.OPENED
    assert outcome.opened is True
    assert legacy_added is False
    assert legacy_detail == "URL ouverte"


def test_resolver_automatic_acquisition_without_manual_prompt(tmp_path: Path, monkeypatch):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = [
        [[]],
        [[]],
        [[]],
        [
            [
                AppleMusicTrack(
                    persistent_id="PID-AUTO",
                    artist="Kyo",
                    title="Dernière danse",
                    query="Dernière danse",
                )
            ]
        ],
    ]
    applescript.acquire_song_from_url.return_value = (
        "duplicated",
        "Duplication automatique vers la bibliothèque effectuée",
    )
    monkeypatch.setattr("playlist_builder.integration.apple_music.resolver.time.sleep", lambda _: None)
    input_mock = MagicMock()
    monkeypatch.setattr("builtins.input", input_mock)

    track = CanonicalTrack(artist=CanonicalArtist(name="Kyo"), title="Dernière danse")
    resolver = AppleMusicResolver(
        applescript,
        identity_cache,
        catalog=FakeCatalog(_catalog_candidate(track)),
        acquire_missing=True,
        wait_for_manual_catalog_add=True,
    )

    outcome = resolver.resolve(track)

    assert outcome.status == AppleMusicResolutionStatus.RESOLVED
    assert outcome.persistent_id == "PID-AUTO"
    assert outcome.catalog_acquired is True
    input_mock.assert_not_called()


def test_resolver_retries_after_manual_acquisition_confirmation(tmp_path: Path, monkeypatch):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = [
        [[]],
        [[]],
        [[]],
        [[]],
        [[]],
        [[AppleMusicTrack(persistent_id="PID-ONE", artist="Daft Punk", title="One More Time", query="One More Time")]],
    ]
    applescript.acquire_song_from_url.return_value = ("opened", "URL ouverte dans Music")
    monkeypatch.setattr("builtins.input", lambda: "")
    monkeypatch.setattr("playlist_builder.integration.apple_music.resolver.time.sleep", lambda _: None)

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
    assert applescript.collect_candidates_batch.call_count == 6


def test_resolver_retries_using_catalog_title_variant(tmp_path: Path, monkeypatch):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    track = CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone")
    catalog_track = CanonicalTrack(
        artist=CanonicalArtist(name="Kygo"),
        title="Firestone (feat. Conrad Sewell)",
    )
    catalog_candidate = CanonicalCandidate(
        track=catalog_track,
        source="itunes_catalog",
        provider_hints=("https://music.apple.com/us/song/firestone/950274258", "itunes_track_id:950274258"),
        raw_confidence=100.0,
        reasons=("test",),
    )
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = [
        [[]],
        [[]],
        [[]],
        [
            [],
            [
                AppleMusicTrack(
                    persistent_id="PID-FEAT",
                    artist="Kygo",
                    title="Firestone (feat. Conrad Sewell)",
                    query="Firestone (feat. Conrad Sewell)",
                )
            ],
        ],
    ]
    applescript.acquire_song_from_url.return_value = ("added", "PID-FEAT")
    monkeypatch.setattr("playlist_builder.integration.apple_music.resolver.time.sleep", lambda _: None)

    resolver = AppleMusicResolver(
        applescript,
        identity_cache,
        catalog=FakeCatalog(catalog_candidate),
        acquire_missing=True,
        wait_for_manual_catalog_add=True,
    )

    outcome = resolver.resolve(track)

    assert outcome.status == AppleMusicResolutionStatus.RESOLVED
    assert outcome.persistent_id == "PID-FEAT"


def test_resolver_acquires_when_library_has_only_false_positives(tmp_path: Path, monkeypatch):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    track = CanonicalTrack(artist=CanonicalArtist(name="Kyo"), title="Dernière danse")
    catalog_candidate = CanonicalCandidate(
        track=track,
        source="itunes_catalog",
        provider_hints=("https://music.apple.com/fr/song/derniere-danse/123",),
        raw_confidence=100.0,
        reasons=("test",),
    )
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = [
        [
            [
                AppleMusicTrack(
                    persistent_id="PID-BAD",
                    artist="Disney",
                    title="Towkyo Takeout",
                    query="Dernière danse",
                )
            ]
        ],
        [[]],
        [[]],
        [
            [
                AppleMusicTrack(
                    persistent_id="PID-KYO",
                    artist="Kyo",
                    title="Dernière danse",
                    query="Dernière danse",
                )
            ]
        ],
    ]
    applescript.acquire_song_from_url.return_value = (
        "duplicated",
        "Duplication automatique vers la bibliothèque effectuée",
    )
    monkeypatch.setattr("playlist_builder.integration.apple_music.resolver.time.sleep", lambda _: None)

    resolver = AppleMusicResolver(
        applescript,
        identity_cache,
        catalog=FakeCatalog(catalog_candidate),
        acquire_missing=True,
        wait_for_manual_catalog_add=False,
    )

    outcome = resolver.resolve(track)

    assert outcome.status == AppleMusicResolutionStatus.RESOLVED
    assert outcome.persistent_id == "PID-KYO"
    assert outcome.catalog_acquired is True
    assert applescript.acquire_song_from_url.called
    assert "Catalogue iTunes" not in outcome.error


def test_resolver_can_open_catalog_without_waiting(tmp_path: Path):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = [
        [[]],
        [[]],
        [[]],
        [[]],
        [[]],
    ]
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
    assert "acquisition automatique" in outcome.error
