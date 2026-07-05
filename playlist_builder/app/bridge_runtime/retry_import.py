"""Retry a subset of playlist tracks without clearing the whole playlist."""

from __future__ import annotations

from collections.abc import Iterator

from playlist_builder.app.factory import AppContext, get_provider_import_port
from playlist_builder.canonical.compat import legacy_track_from_canonical
from playlist_builder.canonical.compat import canonical_playlist_from_legacy
from playlist_builder.core.models import PlaylistDefinition, TrackAddResult, TrackAddStatus
from playlist_builder.ui.bridge.commands import ImportPlaylistResult
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.ui.bridge.events import BridgeEvent, diagnostic_event, progress_event
from playlist_builder.ui.shared.dto.enums import ImportPhase, ImportTrackStatus

from playlist_builder.app.bridge_runtime.import_stream import _emit_track_progress, _final_phase, _flatten_rows
from playlist_builder.app.bridge_runtime.mapping import track_add_results_to_import_state


def stream_retry_import_tracks(
    context: AppContext,
    playlist: PlaylistDefinition,
    request_id: str,
    *,
    track_indices: list[int],
    existing_results: list[TrackAddResult] | None = None,
) -> Iterator[BridgeEvent | ImportPlaylistResult]:
    import sys

    if sys.platform != "darwin":
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            "L'import Apple Music nécessite macOS.",
        )

    if not track_indices:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "Aucun morceau à réessayer.")

    import_port = get_provider_import_port(context)
    labels = import_port.runtime_labels
    rows = _flatten_rows(canonical_playlist_from_legacy(playlist))
    total = len(rows)
    valid_indices = sorted({index for index in track_indices if 0 <= index < total})
    if not valid_indices:
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "Indices de morceaux invalides.")

    merged = _baseline_results(playlist, existing_results)

    yield diagnostic_event(
        request_id,
        phase="retry_start",
        message=f"Nouvelle tentative pour {len(valid_indices)} morceau(x)…",
    )

    existing_keys = {
        f"{item.track.artist.casefold()}:{item.track.title.casefold()}"
        for item in merged
        if item.status == TrackAddStatus.ADDED
    }

    for step, index in enumerate(valid_indices):
        track, section_name = rows[index]
        artist_name = track.artist.display_name
        title_name = track.title
        yield progress_event(
            request_id,
            phase=ImportPhase.RESOLVING.value,
            processed_tracks=step,
            total_tracks=len(valid_indices),
            current_track_label=f"{artist_name} — {title_name}",
            playlist_name=playlist.name,
        )
        yield _emit_track_progress(
            request_id,
            track_index=index,
            total_tracks=total,
            artist=artist_name,
            title=title_name,
            section=section_name,
            step="searching",
            status=ImportTrackStatus.PENDING.value,
            message="Nouvelle recherche…",
        )
        outcome = import_port.resolve(track, section=section_name)
        yield _emit_track_progress(
            request_id,
            track_index=index,
            total_tracks=total,
            artist=artist_name,
            title=title_name,
            section=section_name,
            step="resolving",
            status=ImportTrackStatus.PENDING.value,
            message="Résolution…",
        )

        yield progress_event(
            request_id,
            phase=ImportPhase.DELIVERING.value,
            processed_tracks=step,
            total_tracks=len(valid_indices),
            playlist_name=playlist.name,
        )
        import_port.ensure_playlist(playlist.name)
        canonical_result = import_port.add_resolved_track(
            playlist.name,
            outcome,
            section_name=section_name,
            existing_keys=existing_keys,
        )
        legacy_track = legacy_track_from_canonical(track, section=section_name)
        merged[index] = TrackAddResult(
            track=legacy_track,
            status=_map_canonical_status(canonical_result.status),
            error=canonical_result.error or "",
        )
        if merged[index].status == TrackAddStatus.ADDED:
            existing_keys.add(f"{legacy_track.artist.casefold()}:{legacy_track.title.casefold()}")

        final_status = _map_track_status(merged[index].status)
        yield _emit_track_progress(
            request_id,
            track_index=index,
            total_tracks=total,
            artist=artist_name,
            title=title_name,
            section=section_name,
            step="completed",
            status=final_status.value,
            message=merged[index].error or _status_message(final_status, labels.not_found_message),
        )

    phase = _final_phase(merged)
    import_state = track_add_results_to_import_state(playlist.name, merged, phase=phase)
    yield ImportPlaylistResult(import_result=import_state)


def _baseline_results(
    playlist: PlaylistDefinition,
    existing_results: list[TrackAddResult] | None,
) -> list[TrackAddResult]:
    rows = []
    for section in playlist.sections:
        for track in section.tracks:
            rows.append(track)
    if existing_results and len(existing_results) == len(rows):
        return list(existing_results)
    return [
        TrackAddResult(track=track, status=TrackAddStatus.NOT_FOUND, error="Non importé")
        for track in rows
    ]


def _map_canonical_status(status):
    from playlist_builder.canonical.enums import ImportStatus

    return {
        ImportStatus.ADDED: TrackAddStatus.ADDED,
        ImportStatus.SKIPPED: TrackAddStatus.SKIPPED,
        ImportStatus.NOT_FOUND: TrackAddStatus.NOT_FOUND,
        ImportStatus.ERROR: TrackAddStatus.ERROR,
    }[status]


def _map_track_status(status: TrackAddStatus) -> ImportTrackStatus:
    return {
        TrackAddStatus.ADDED: ImportTrackStatus.ADDED,
        TrackAddStatus.SKIPPED: ImportTrackStatus.SKIPPED,
        TrackAddStatus.NOT_FOUND: ImportTrackStatus.NOT_FOUND,
        TrackAddStatus.ERROR: ImportTrackStatus.ERROR,
    }[status]


def _status_message(status: ImportTrackStatus, not_found_message: str) -> str:
    return {
        ImportTrackStatus.ADDED: "Ajouté",
        ImportTrackStatus.SKIPPED: "Déjà présent",
        ImportTrackStatus.NOT_FOUND: not_found_message,
        ImportTrackStatus.ERROR: "Erreur",
    }[status]
