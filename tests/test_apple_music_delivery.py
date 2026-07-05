from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from playlist_builder.canonical.enums import ImportStatus, ProviderId
from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalImportReport,
    CanonicalPlaylist,
    CanonicalPlaylistSection,
    CanonicalTrack,
)
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
from playlist_builder.integration.apple_music.delivery import AppleMusicDelivery
from playlist_builder.integration.apple_music.import_service import AppleMusicImportService
from playlist_builder.integration.apple_music.resolver import (
    AppleMusicResolutionOutcome,
    AppleMusicResolutionStatus,
)


def _track() -> CanonicalTrack:
    return CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone")


def _playlist() -> CanonicalPlaylist:
    track = _track()
    return CanonicalPlaylist(
        name="E2E Test",
        sections=(CanonicalPlaylistSection(name="Playlist", tracks=(track,)),),
    )


def _resolved_outcome() -> AppleMusicResolutionOutcome:
    return AppleMusicResolutionOutcome(
        track=_track(),
        persistent_id="PID123",
        status=AppleMusicResolutionStatus.RESOLVED,
        score=95.0,
    )


def test_delivery_adds_resolved_track():
    applescript = MagicMock()
    applescript.add_tracks_by_persistent_id_batch.return_value = ["added\x1ePID123"]
    applescript.count_playlist_tracks.return_value = 1
    delivery = AppleMusicDelivery(applescript)

    report = delivery.sync_playlist(_playlist(), [_resolved_outcome()])

    assert report.results[0].status == ImportStatus.ADDED
    applescript.clear_playlist_tracks.assert_called_once_with("E2E Test")
    applescript.count_playlist_tracks.assert_called()


def test_delivery_retries_not_found_batch_status():
    applescript = MagicMock()
    applescript.add_tracks_by_persistent_id_batch.side_effect = [
        ["not_found\x1ePID123"],
        ["added\x1ePID123"],
    ]
    applescript.count_playlist_tracks.return_value = 1
    delivery = AppleMusicDelivery(applescript)

    report = delivery.sync_playlist(_playlist(), [_resolved_outcome()])

    assert report.results[0].status == ImportStatus.ADDED
    assert applescript.add_tracks_by_persistent_id_batch.call_count == 2


def test_delivery_marks_unresolved_track_as_not_found():
    applescript = MagicMock()
    delivery = AppleMusicDelivery(applescript)
    outcome = AppleMusicResolutionOutcome(
        track=_track(),
        persistent_id=None,
        status=AppleMusicResolutionStatus.NOT_FOUND,
    )

    report = delivery.sync_playlist(_playlist(), [outcome])

    assert report.results[0].status == ImportStatus.NOT_FOUND
    applescript.clear_playlist_tracks.assert_not_called()
    applescript.add_tracks_by_persistent_id_batch.assert_not_called()


def test_delivery_skips_clear_when_no_resolved_tracks():
    applescript = MagicMock()
    delivery = AppleMusicDelivery(applescript)
    outcome = AppleMusicResolutionOutcome(
        track=_track(),
        persistent_id=None,
        status=AppleMusicResolutionStatus.NOT_FOUND,
        error="Acquisition échouée.",
    )

    delivery.sync_playlist(_playlist(), [outcome])

    applescript.clear_playlist_tracks.assert_not_called()


def test_delivery_aligns_when_outcome_count_is_shorter_than_playlist():
    applescript = MagicMock()
    applescript.add_tracks_by_persistent_id_batch.return_value = ["added"]
    delivery = AppleMusicDelivery(applescript)
    playlist = CanonicalPlaylist(
        name="Mismatch",
        sections=(
            CanonicalPlaylistSection(
                name="Playlist",
                tracks=(_track(), CanonicalTrack(artist=CanonicalArtist(name="Daft Punk"), title="One More Time")),
            ),
        ),
    )

    report = delivery.sync_playlist(playlist, [_resolved_outcome()])

    assert len(report.results) == 2
    assert report.results[0].status == ImportStatus.ADDED
    assert report.results[1].status == ImportStatus.ERROR


def test_import_service_uses_cache_on_second_run(tmp_path: Path):
    applescript = MagicMock()
    applescript.collect_candidates_batch.return_value = [
        [
            __import__(
                "playlist_builder.integration.apple_music.models",
                fromlist=["AppleMusicTrack"],
            ).AppleMusicTrack(
                persistent_id="PID123",
                artist="Kygo",
                title="Firestone",
                query="Kygo Firestone",
            )
        ]
    ]
    applescript.add_tracks_by_persistent_id_batch.return_value = ["added\x1ePID123"]
    applescript.count_playlist_tracks.return_value = 1
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    service = AppleMusicImportService(applescript, identity_cache)
    playlist = _playlist()

    first = service.import_playlist(playlist, sync=True)
    second = service.import_playlist(playlist, sync=True)

    assert first.results[0].status == ImportStatus.ADDED
    assert second.results[0].status == ImportStatus.ADDED
    assert applescript.collect_candidates_batch.call_count == 1


def test_import_service_preserves_section_order():
    applescript = MagicMock()
    applescript.add_tracks_by_persistent_id_batch.return_value = ["added\x1e1", "added\x1e2"]
    applescript.count_playlist_tracks.return_value = 2
    service = AppleMusicImportService(applescript, IdentityCache(MagicMock()))
    playlist = CanonicalPlaylist(
        name="Sections",
        sections=(
            CanonicalPlaylistSection(
                name="Warm Up",
                tracks=(
                    CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone"),
                ),
            ),
            CanonicalPlaylistSection(
                name="Peak",
                tracks=(
                    CanonicalTrack(artist=CanonicalArtist(name="Avicii"), title="Levels"),
                ),
            ),
        ),
    )
    applescript.collect_candidates_batch.return_value = [[], []]
    service._resolver.resolve_batch = MagicMock(
        return_value=[
            AppleMusicResolutionOutcome(
                track=playlist.sections[0].tracks[0],
                persistent_id="PID1",
                status=AppleMusicResolutionStatus.RESOLVED,
                score=90.0,
            ),
            AppleMusicResolutionOutcome(
                track=playlist.sections[1].tracks[0],
                persistent_id="PID2",
                status=AppleMusicResolutionStatus.RESOLVED,
                score=90.0,
            ),
        ]
    )

    report = service.import_playlist(playlist, sync=True)

    assert [item.section_name for item in report.results] == ["Warm Up", "Peak"]
