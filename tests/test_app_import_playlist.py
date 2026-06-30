from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from playlist_builder.app import AppSettings, build_app_context
from playlist_builder.app.use_cases.import_playlist import ImportPlaylistUseCase
from playlist_builder.canonical.enums import ImportStatus
from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalImportReport,
    CanonicalImportResult,
    CanonicalPlaylist,
    CanonicalPlaylistSection,
    CanonicalTrack,
)
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackRef


def _playlist() -> PlaylistDefinition:
    return PlaylistDefinition(
        name="E2E Test",
        sections=(
            PlaylistSection(
                name="Playlist",
                tracks=(TrackRef("Kygo", "Firestone", section="Playlist"),),
            ),
        ),
    )


def test_import_playlist_use_case_routes_through_gateway(tmp_path: Path):
    context = build_app_context(
        AppSettings(
            identity_cache_path=tmp_path / "identity.json",
            catalog_cache_path=tmp_path / "catalog.json",
            acquire_missing_from_catalog=False,
        )
    )
    canonical = CanonicalPlaylist(
        name="E2E Test",
        sections=(
            CanonicalPlaylistSection(
                name="Playlist",
                tracks=(CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone"),),
            ),
        ),
    )
    expected = CanonicalImportReport(
        playlist_name="E2E Test",
        results=(
            CanonicalImportResult(
                track=canonical.tracks[0],
                status=ImportStatus.ADDED,
                section_name="Playlist",
            ),
        ),
    )
    context.apple_music.import_service.import_playlist = MagicMock(return_value=expected)
    result = ImportPlaylistUseCase(context).execute(_playlist(), sync=True, write_json_diagnostics=True)

    assert result.track_results[0].track.title == "Firestone"
    assert result.text_report_path.exists()
    assert result.json_report_path is not None
    assert result.json_report_path.exists()
