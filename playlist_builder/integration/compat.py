from __future__ import annotations

from playlist_builder.canonical.compat import legacy_track_from_canonical
from playlist_builder.canonical.enums import ImportStatus
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalImportResult
from playlist_builder.core.models import TrackAddResult, TrackAddStatus, TrackRef


def canonical_import_report_to_track_results(
    report: CanonicalImportReport,
) -> list[TrackAddResult]:
    results: list[TrackAddResult] = []
    for item in report.results:
        results.append(canonical_import_result_to_track_result(item))
    return results


def canonical_import_result_to_track_result(item: CanonicalImportResult) -> TrackAddResult:
    track = legacy_track_from_canonical(item.track, section=item.section_name)
    status = _map_import_status(item.status)
    return TrackAddResult(track=track, status=status, error=item.error)


def track_results_aligned_with_playlist(
    playlist_tracks: list[TrackRef],
    report: CanonicalImportReport,
) -> list[TrackAddResult]:
    by_key = {item.track.identity_key: item for item in report.results}
    aligned: list[TrackAddResult] = []
    for track in playlist_tracks:
        canonical_key = track.to_canonical().identity_key
        item = by_key.get(canonical_key)
        if item is None:
            aligned.append(
                TrackAddResult(
                    track=track,
                    status=TrackAddStatus.ERROR,
                    error="Résultat d'import manquant pour ce morceau.",
                )
            )
            continue
        result = canonical_import_result_to_track_result(item)
        aligned.append(
            TrackAddResult(
                track=TrackRef(
                    artist=result.track.artist,
                    title=result.track.title,
                    section=track.section,
                ),
                status=result.status,
                error=result.error,
            )
        )
    return aligned


def _map_import_status(status: ImportStatus) -> TrackAddStatus:
    return {
        ImportStatus.ADDED: TrackAddStatus.ADDED,
        ImportStatus.NOT_FOUND: TrackAddStatus.NOT_FOUND,
        ImportStatus.SKIPPED: TrackAddStatus.SKIPPED,
        ImportStatus.ERROR: TrackAddStatus.ERROR,
    }[status]
