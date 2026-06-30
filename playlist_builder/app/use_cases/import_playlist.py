from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from playlist_builder.app.factory import AppContext
from playlist_builder.canonical.compat import canonical_playlist_from_legacy
from playlist_builder.core.models import PlaylistDefinition, TrackAddResult, TrackRef
from playlist_builder.integration.compat import track_results_aligned_with_playlist
from playlist_builder.reports.import_diagnostics import write_import_diagnostics
from playlist_builder.reports.playlist import write_playlist_report


@dataclass(frozen=True, slots=True)
class ImportPlaylistResult:
    playlist_name: str
    track_results: tuple[TrackAddResult, ...]
    text_report_path: Path
    json_report_path: Path | None = None


class ImportPlaylistUseCase:
    """Import a legacy playlist definition into Apple Music via the integration gateway."""

    def __init__(self, context: AppContext) -> None:
        self._context = context

    def execute(
        self,
        playlist: PlaylistDefinition,
        *,
        sync: bool = True,
        existing_keys: set[str] | None = None,
        allow_duplicates: bool = False,
        write_json_diagnostics: bool = True,
    ) -> ImportPlaylistResult:
        canonical = canonical_playlist_from_legacy(playlist)
        apple = self._context.apple_music

        if sync:
            report = self._context.gateway.import_playlist(canonical, sync=True)
        else:
            report = apple.import_service.import_playlist(
                canonical,
                sync=False,
                existing_keys=existing_keys,
                allow_duplicates=allow_duplicates,
            )

        aligned = track_results_aligned_with_playlist(playlist.tracks, report)
        text_report = write_playlist_report(playlist.name, aligned, Path("reports"))
        json_report = None
        if write_json_diagnostics:
            json_report = write_import_diagnostics(
                playlist.name,
                report,
                aligned,
                Path("reports"),
            )

        apple.import_service.identity_cache.flush()
        if self._context.settings.use_catalog_cache:
            cache = self._context.apple_music.catalog.client.cache
            if cache is not None:
                cache.flush()

        return ImportPlaylistResult(
            playlist_name=playlist.name,
            track_results=tuple(aligned),
            text_report_path=text_report,
            json_report_path=json_report,
        )
