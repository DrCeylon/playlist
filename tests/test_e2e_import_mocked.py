from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from playlist_builder.canonical.compat import canonical_playlist_from_legacy
from playlist_builder.canonical.enums import ImportStatus
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalImportResult
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackAddStatus, TrackRef
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.integration.compat import track_results_aligned_with_playlist
from playlist_builder.music.client import MusicClient


def test_mocked_e2e_kygo_firestone_is_added(tmp_path: Path):
    playlist = PlaylistDefinition(
        name="E2E Test",
        sections=(
            PlaylistSection(
                name="Playlist",
                tracks=(TrackRef("Kygo", "Firestone", section="Playlist"),),
            ),
        ),
    )
    applescript = MagicMock()
    applescript.collect_candidates_batch.return_value = [
        [AppleMusicTrack(persistent_id="PID123", artist="Kygo", title="Firestone", query="Kygo Firestone")]
    ]
    applescript.add_tracks_by_persistent_id_batch.return_value = ["added\x1ePID123"]
    applescript.count_playlist_tracks.return_value = 1

    from playlist_builder.catalog.cache import JsonCache
    from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
    from playlist_builder.integration.apple_music.import_service import AppleMusicImportService

    service = AppleMusicImportService(applescript, IdentityCache(JsonCache(tmp_path / "identity.json")))
    canonical = canonical_playlist_from_legacy(playlist)

    first_report = service.import_playlist(canonical, sync=True)
    first_results = track_results_aligned_with_playlist(playlist.tracks, first_report)

    assert first_results[0].status == TrackAddStatus.ADDED

    second_report = service.import_playlist(canonical, sync=True)
    second_results = track_results_aligned_with_playlist(playlist.tracks, second_report)

    assert second_results[0].status == TrackAddStatus.ADDED
    assert applescript.collect_candidates_batch.call_count == 1


def test_music_client_batch_uses_resolver_and_delivery(tmp_path: Path):
    client = MusicClient(identity_cache_path=tmp_path / "identity.json")
    tracks = [TrackRef("Kygo", "Firestone")]

    with (
        patch.object(client._service.resolver, "resolve_batch") as resolve_mock,
        patch.object(client._applescript, "add_tracks_by_persistent_id_batch", return_value=["added\x1ePID"]) as add_mock,
    ):
        from playlist_builder.integration.apple_music.resolver import (
            AppleMusicResolutionOutcome,
            AppleMusicResolutionStatus,
        )

        resolve_mock.return_value = [
            AppleMusicResolutionOutcome(
                track=tracks[0].to_canonical(),
                persistent_id="PID",
                status=AppleMusicResolutionStatus.RESOLVED,
                score=90.0,
            )
        ]
        results = client._add_tracks_batch("Test", tracks)

    assert results[0].status == TrackAddStatus.ADDED
    add_mock.assert_called_once_with("Test", ["PID"])
