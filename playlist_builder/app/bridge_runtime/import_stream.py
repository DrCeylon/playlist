from __future__ import annotations

import time
from collections.abc import Iterator

from playlist_builder.app.factory import AppContext, get_provider_import_port
from playlist_builder.canonical.compat import canonical_playlist_from_legacy
from playlist_builder.core.models import PlaylistDefinition, TrackAddResult, TrackAddStatus
from playlist_builder.integration.ports.provider_import import ProviderImportResolutionStatus
from playlist_builder.integration.compat import track_results_aligned_with_playlist
from playlist_builder.ui.bridge.commands import ImportPlaylistResult
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.ui.bridge.events import (
    BridgeEvent,
    diagnostic_event,
    manual_acquisition_required_event,
    progress_event,
    track_progress_event,
)
from playlist_builder.infrastructure.perf import PerfSession, perf_record, perf_span, perf_trace_enabled
from playlist_builder.app.bridge_runtime.import_session import ImportSessionCheckpoint, ImportSessionStore, new_session_id
from playlist_builder.app.bridge_runtime.manual_gate import ManualAcquisitionInterrupted
from playlist_builder.app.bridge_runtime.mapping import track_add_results_to_import_state
from playlist_builder.infrastructure.manual_continue_trace import log as manual_continue_trace
from playlist_builder.ui.shared.dto.enums import ImportPhase, ImportTrackStatus

RESOLVE_BATCH_SIZE = 5


def _track_key(index: int, artist: str, title: str) -> str:
    return f"{index}:{artist.strip().casefold()}:{title.strip().casefold()}"


def _emit_track_progress(
    request_id: str,
    *,
    track_index: int,
    total_tracks: int,
    artist: str,
    title: str,
    section: str,
    step: str,
    status: str,
    message: str = "",
    album: str = "",
    catalog_url: str = "",
    added_count: int = 0,
    skipped_count: int = 0,
    not_found_count: int = 0,
    error_count: int = 0,
) -> BridgeEvent:
    return track_progress_event(
        request_id,
        track_key=_track_key(track_index, artist, title),
        track_index=track_index,
        total_tracks=total_tracks,
        artist=artist,
        title=title,
        section=section,
        step=step,
        status=status,
        message=message,
        album=album,
        catalog_url=catalog_url,
        is_current=True,
        added_count=added_count,
        skipped_count=skipped_count,
        not_found_count=not_found_count,
        error_count=error_count,
    )


def _import_log(message: str) -> None:
    import sys

    print(f"resonance-import: {message}", file=sys.stderr, flush=True)


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def _timed_message(started_at: float, message: str) -> str:
    return f"[+{_elapsed_ms(started_at)} ms] {message}"


def stream_import_playlist(
    context: AppContext,
    playlist: PlaylistDefinition,
    request_id: str,
    *,
    sync: bool,
    write_json_diagnostics: bool,
    session_store: ImportSessionStore,
    checkpoint: ImportSessionCheckpoint | None = None,
    history_session_id: str = "",
) -> Iterator[BridgeEvent | ImportPlaylistResult]:
    import sys

    if sys.platform != "darwin":
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            "L'import Apple Music nécessite macOS.",
        )

    import_port = get_provider_import_port(context)
    labels = import_port.runtime_labels

    if context.settings.wait_for_manual_catalog_add:
        from playlist_builder.app.bridge_runtime.manual_gate import (
            ManualAcquisitionGate,
            confirmed_manual_acquisition_hook,
        )

        if checkpoint is None:
            import_port.configure_manual_acquisition(ManualAcquisitionGate().hook)
        else:
            import_port.configure_manual_acquisition(confirmed_manual_acquisition_hook)
    if checkpoint is not None:
        manual_continue_trace(
            f"ENTER stream_import_playlist(resume) session_id={checkpoint.session_id} next_index={checkpoint.next_index}"
        )
        playlist = checkpoint.playlist
        request_id = checkpoint.request_id
        sync = checkpoint.sync
        write_json_diagnostics = checkpoint.write_json_diagnostics
        start_index = checkpoint.next_index
        session_id = checkpoint.session_id
        history_session_id = checkpoint.history_session_id or history_session_id
    else:
        start_index = 0
        session_id = new_session_id()

    canonical = canonical_playlist_from_legacy(playlist)
    rows = _flatten_rows(canonical)
    total = len(rows)
    cache_mode = "warm" if perf_trace_enabled() else ""
    with PerfSession(
        scenario="import",
        operation="import_playlist",
        track_count=total,
        cache_mode=cache_mode,
    ) as perf_session:
        yield from _stream_import_playlist_body(
            context=context,
            playlist=playlist,
            request_id=request_id,
            sync=sync,
            write_json_diagnostics=write_json_diagnostics,
            session_store=session_store,
            checkpoint=checkpoint,
            import_port=import_port,
            labels=labels,
            canonical=canonical,
            rows=rows,
            total=total,
            start_index=start_index,
            session_id=session_id,
            history_session_id=history_session_id,
            perf_session=perf_session,
        )


def _stream_import_playlist_body(
    *,
    context: AppContext,
    playlist: PlaylistDefinition,
    request_id: str,
    sync: bool,
    write_json_diagnostics: bool,
    session_store: ImportSessionStore,
    checkpoint: ImportSessionCheckpoint | None,
    import_port,
    labels,
    canonical,
    rows: list,
    total: int,
    start_index: int,
    session_id: str,
    history_session_id: str,
    perf_session: PerfSession,
) -> Iterator[BridgeEvent | ImportPlaylistResult]:
    import_started_at = time.perf_counter()

    yield diagnostic_event(
        request_id,
        phase="import_start",
        message=_timed_message(import_started_at, f"Commande import_playlist reçue — {total} morceau(x) à traiter"),
    )
    _import_log(f"playlist={playlist.name!r} tracks={total} history_session pending")
    yield diagnostic_event(
        request_id,
        phase="music_app",
        message=_timed_message(import_started_at, labels.connect_message),
    )
    _import_log(f"{labels.runtime_app_name} ensure_running")
    music_app_started = time.perf_counter()
    try:
        import_port.ensure_runtime_ready(activate=False)
    except RuntimeError as exc:
        _import_log(f"{labels.runtime_app_name} ensure_running failed: {exc}")
        raise BridgeError(BridgeErrorCode.PROVIDER_UNAVAILABLE, str(exc)) from exc
    music_app_ms = int((time.perf_counter() - music_app_started) * 1000)
    perf_record("import", "music_app_ensure", music_app_ms)
    _import_log(f"{labels.runtime_app_name} ensure_running OK ({music_app_ms} ms)")
    yield diagnostic_event(
        request_id,
        phase="music_app",
        message=_timed_message(
            import_started_at,
            labels.runtime_ready_message.format(duration_ms=music_app_ms),
        ),
    )

    resolve_phase_started = time.perf_counter()

    yield progress_event(
        request_id,
        phase=ImportPhase.RESOLVING.value,
        processed_tracks=start_index,
        total_tracks=total,
        playlist_name=playlist.name,
        import_session_id=session_id,
    )

    outcomes: list = []
    if checkpoint is not None and start_index > 0:
        outcomes = _prefill_resolved_outcomes_before_checkpoint(import_port, rows, start_index)
        manual_continue_trace(
            f"CALL stream_import_playlist(resume) prefilled_outcomes={len(outcomes)} start_index={start_index}"
        )
    added_count = 0
    skipped_count = 0
    not_found_count = 0
    error_count = 0
    index = start_index
    while index < total:
        batch_end = min(index + RESOLVE_BATCH_SIZE, total)
        batch_rows = rows[index:batch_end]
        batch_inputs: list[tuple[int, object, str]] = []
        for offset, (track, section_name) in enumerate(batch_rows):
            track_index = index + offset
            batch_inputs.append((track_index, track, section_name))

        if batch_inputs:
            batch_number = (index // RESOLVE_BATCH_SIZE) + 1
            for track_index, track, section_name in batch_inputs:
                artist_name = track.artist.display_name
                title_name = track.title
                yield _emit_track_progress(
                    request_id,
                    track_index=track_index,
                    total_tracks=total,
                    artist=artist_name,
                    title=title_name,
                    section=section_name,
                    step="searching",
                    status=ImportTrackStatus.PENDING.value,
                    message="Recherche…",
                    added_count=added_count,
                    skipped_count=skipped_count,
                    not_found_count=not_found_count,
                    error_count=error_count,
                )

            try:
                with perf_span(
                    "import",
                    "resolve_batch",
                    batch_index=batch_number,
                    metadata={"batch_size": len(batch_inputs)},
                ):
                    resolved_batch = import_port.resolve_batch(
                        [(track, section_name) for _, track, section_name in batch_inputs]
                    )
            except ManualAcquisitionInterrupted as pause:
                track_index = next(
                    (
                        idx
                        for idx, track, _section in batch_inputs
                        if track.artist.display_name == pause.artist and track.title == pause.title
                    ),
                    batch_inputs[0][0],
                )
                _, _track, section_name = next(item for item in batch_inputs if item[0] == track_index)
                session_store.save(
                    ImportSessionCheckpoint(
                        session_id=session_id,
                        playlist=playlist,
                        next_index=track_index,
                        request_id=request_id,
                        sync=sync,
                        write_json_diagnostics=write_json_diagnostics,
                        history_session_id=history_session_id,
                    )
                )
                yield manual_acquisition_required_event(
                    request_id,
                    token=pause.token,
                    artist=pause.artist,
                    title=pause.title,
                    instructions=pause.instructions,
                    catalog_label=pause.catalog_label,
                    catalog_url=pause.catalog_url,
                    album=pause.album,
                    import_session_id=session_id,
                )
                yield _emit_track_progress(
                    request_id,
                    track_index=track_index,
                    total_tracks=total,
                    artist=pause.artist,
                    title=pause.title,
                    section=section_name,
                    step="acquiring",
                    status=ImportTrackStatus.ACQUIRING.value,
                    message="Acquisition manuelle requise",
                    album=pause.album,
                    catalog_url=pause.catalog_url,
                    added_count=added_count,
                    skipped_count=skipped_count,
                    not_found_count=not_found_count,
                    error_count=error_count,
                )
                from playlist_builder.ui.shared.dto.import_state import ImportResultState, ImportTrackOutcome

                import_state = ImportResultState(
                    playlist_name=playlist.name,
                    outcomes=(
                        ImportTrackOutcome(
                            pause.artist,
                            pause.title,
                            section_name,
                            ImportTrackStatus.ACQUIRING,
                            pause.instructions,
                        ),
                    ),
                    phase=ImportPhase.WAITING_FOR_MANUAL_ACQUISITION,
                    import_session_id=session_id,
                    manual_token=pause.token,
                    manual_artist=pause.artist,
                    manual_title=pause.title,
                    manual_instructions=pause.instructions,
                    manual_catalog_label=pause.catalog_label,
                    manual_catalog_url=pause.catalog_url,
                    manual_album=pause.album,
                )
                yield ImportPlaylistResult(import_result=import_state)
                return

            for (track_index, track, section_name), outcome in zip(
                batch_inputs, resolved_batch, strict=True
            ):
                artist_name = track.artist.display_name
                title_name = track.title
                label = f"{artist_name} — {title_name}"
                yield progress_event(
                    request_id,
                    phase=ImportPhase.RESOLVING.value,
                    processed_tracks=track_index,
                    total_tracks=total,
                    current_track_label=label,
                    import_session_id=session_id,
                    added_count=added_count,
                    skipped_count=skipped_count,
                    not_found_count=not_found_count,
                    error_count=error_count,
                )
                yield _emit_track_progress(
                    request_id,
                    track_index=track_index,
                    total_tracks=total,
                    artist=artist_name,
                    title=title_name,
                    section=section_name,
                    step="resolving",
                    status=ImportTrackStatus.PENDING.value,
                    message="Résolution…",
                    added_count=added_count,
                    skipped_count=skipped_count,
                    not_found_count=not_found_count,
                    error_count=error_count,
                )
                yield diagnostic_event(
                    request_id,
                    phase="resolve",
                    message=f"Résolution du morceau : {label}",
                )
                _import_log(f"resolve {track_index + 1}/{total}: {label}")

                track_status = ImportTrackStatus.PENDING
                track_message = "Résolu"
                if outcome.status == ProviderImportResolutionStatus.NOT_FOUND:
                    not_found_count += 1
                    track_status = ImportTrackStatus.NOT_FOUND
                    track_message = outcome.error or labels.not_found_message
                elif outcome.status == ProviderImportResolutionStatus.ERROR:
                    error_count += 1
                    track_status = ImportTrackStatus.ERROR
                    track_message = outcome.error or "Erreur de résolution"
                elif outcome.cache_hit:
                    track_message = "Trouvé (cache)"
                elif outcome.catalog_acquired:
                    yield _emit_track_progress(
                        request_id,
                        track_index=track_index,
                        total_tracks=total,
                        artist=artist_name,
                        title=title_name,
                        section=section_name,
                        step="acquiring",
                        status=ImportTrackStatus.PENDING.value,
                        message="Acquisition catalogue…",
                        added_count=added_count,
                        skipped_count=skipped_count,
                        not_found_count=not_found_count,
                        error_count=error_count,
                    )
                    track_message = "Acquis depuis le catalogue"

                yield _emit_track_progress(
                    request_id,
                    track_index=track_index,
                    total_tracks=total,
                    artist=artist_name,
                    title=title_name,
                    section=section_name,
                    step="completed",
                    status=track_status.value,
                    message=track_message,
                    added_count=added_count,
                    skipped_count=skipped_count,
                    not_found_count=not_found_count,
                    error_count=error_count,
                )
                if outcome.cache_hit:
                    yield diagnostic_event(
                        request_id,
                        phase="cache_hit",
                        message=f"Cache IdentityCache : {label}",
                        artist=artist_name,
                        title=title_name,
                    )
                elif outcome.catalog_acquired:
                    yield diagnostic_event(
                        request_id,
                        phase="catalog_lookup",
                        message=f"Acquisition catalogue : {label}",
                        artist=artist_name,
                        title=title_name,
                    )
                elif outcome.status == ProviderImportResolutionStatus.NOT_FOUND:
                    yield diagnostic_event(
                        request_id,
                        phase="catalog_lookup",
                        message=outcome.error or f"Introuvable : {label}",
                        artist=artist_name,
                        title=title_name,
                    )
                outcomes.append((outcome, section_name))
                yield progress_event(
                    request_id,
                    phase=ImportPhase.RESOLVING.value,
                    processed_tracks=track_index + 1,
                    total_tracks=total,
                    current_track_label=label,
                    import_session_id=session_id,
                    added_count=added_count,
                    skipped_count=skipped_count,
                    not_found_count=not_found_count,
                    error_count=error_count,
                )
        index = batch_end

    resolve_ms = int((time.perf_counter() - resolve_phase_started) * 1000)
    perf_record("import", "resolve_total", resolve_ms, metadata={"track_count": total})
    yield diagnostic_event(
        request_id,
        phase="resolve",
        message=_timed_message(
            import_started_at,
            f"Résolution terminée en {resolve_ms} ms pour {total} morceau(x)",
        ),
    )

    yield progress_event(
        request_id,
        phase=ImportPhase.DELIVERING.value,
        processed_tracks=0,
        total_tracks=total,
        playlist_name=playlist.name,
        import_session_id=session_id,
        added_count=added_count,
        skipped_count=skipped_count,
        not_found_count=not_found_count,
        error_count=error_count,
    )

    yield diagnostic_event(
        request_id,
        phase="delivering",
        message=labels.delivery_start_message.format(playlist_name=playlist.name),
    )
    _import_log(f"ensure_playlist name={playlist.name!r}")

    delivery_started = time.perf_counter()
    delivery_progress_events: list[tuple[int, int]] = []

    def on_delivery_batch(current_batch: int, total_batches: int) -> None:
        delivery_progress_events.append((current_batch, total_batches))

    try:
        import_port.ensure_playlist(playlist.name)
        _import_log("sync_playlist starting")
        report = import_port.deliver_playlist(
            canonical,
            [item[0] for item in outcomes],
            on_delivery_batch=on_delivery_batch,
        )
        _import_log("sync_playlist finished")
    except ValueError as exc:
        _import_log(f"sync_playlist alignment failed: {exc}")
        raise BridgeError(
            BridgeErrorCode.ENGINE_ERROR,
            "Impossible de finaliser l'import : les morceaux résolus ne correspondent pas à la playlist. Relance l'import ou régénère la playlist.",
        ) from exc
    except RuntimeError as exc:
        _import_log(f"delivery failed: {exc}")
        raise BridgeError(BridgeErrorCode.PROVIDER_UNAVAILABLE, str(exc)) from exc

    for batch_index, batch_count in delivery_progress_events:
        processed = min(total, max(1, int(total * (0.7 + 0.3 * batch_index / max(batch_count, 1)))))
        yield progress_event(
            request_id,
            phase=ImportPhase.DELIVERING.value,
            processed_tracks=processed,
            total_tracks=total,
            playlist_name=playlist.name,
            import_session_id=session_id,
            current_track_label=labels.delivery_batch_message.format(
                batch_index=batch_index,
                batch_count=batch_count,
            ),
            added_count=added_count,
            skipped_count=skipped_count,
            not_found_count=not_found_count,
            error_count=error_count,
        )
        yield diagnostic_event(
            request_id,
            phase="delivering",
            message=labels.delivery_batch_message.format(
                batch_index=batch_index,
                batch_count=batch_count,
            ),
        )

    delivery_ms = int((time.perf_counter() - delivery_started) * 1000)
    perf_record("import", "delivery_total", delivery_ms, metadata={"track_count": total})
    yield diagnostic_event(
        request_id,
        phase="delivering",
        message=_timed_message(
            import_started_at,
            labels.delivery_complete_message.format(duration_ms=delivery_ms),
        ),
    )

    aligned = track_results_aligned_with_playlist(playlist.tracks, report)
    added_count = 0
    skipped_count = 0
    not_found_count = 0
    error_count = 0
    for index, item in enumerate(aligned):
        track = item.track
        if item.status == TrackAddStatus.ADDED:
            added_count += 1
            step_status = ImportTrackStatus.ADDED
            message = "Ajouté"
        elif item.status == TrackAddStatus.SKIPPED:
            skipped_count += 1
            step_status = ImportTrackStatus.SKIPPED
            message = item.error or "Déjà présent"
        elif item.status == TrackAddStatus.NOT_FOUND:
            not_found_count += 1
            step_status = ImportTrackStatus.NOT_FOUND
            message = item.error or "Introuvable"
        else:
            error_count += 1
            step_status = ImportTrackStatus.ERROR
            message = item.error or "Erreur"
        yield _emit_track_progress(
            request_id,
            track_index=index,
            total_tracks=total,
            artist=track.artist,
            title=track.title,
            section=track.section,
            step="adding" if step_status == ImportTrackStatus.ADDED else "completed",
            status=step_status.value,
            message=message,
            added_count=added_count,
            skipped_count=skipped_count,
            not_found_count=not_found_count,
            error_count=error_count,
        )
        if step_status == ImportTrackStatus.ADDED:
            yield _emit_track_progress(
                request_id,
                track_index=index,
                total_tracks=total,
                artist=track.artist,
                title=track.title,
                section=track.section,
                step="completed",
                status=step_status.value,
                message=message,
                added_count=added_count,
                skipped_count=skipped_count,
                not_found_count=not_found_count,
                error_count=error_count,
            )

    if added_count > 0:
        yield diagnostic_event(
            request_id,
            phase="delivering",
            message=labels.delivery_confirm_message.format(added_count=added_count),
        )
    if write_json_diagnostics:
        try:
            from pathlib import Path

            from playlist_builder.reports.import_diagnostics import write_import_diagnostics
            from playlist_builder.reports.playlist import write_playlist_report

            write_playlist_report(playlist.name, aligned, Path("reports"))
            write_import_diagnostics(playlist.name, report, aligned, Path("reports"))
        except OSError as exc:
            _import_log(f"report write failed: {exc}")
            yield diagnostic_event(
                request_id,
                phase="delivering",
                message="Import terminé — écriture des rapports locaux impossible.",
            )

    try:
        context.gateway.flush_caches(flush_catalog_cache=context.settings.use_catalog_cache)
    except Exception as exc:
        _import_log(f"cache flush failed: {exc}")

    try:
        session_store.delete(session_id)
    except OSError as exc:
        _import_log(f"session cleanup failed: {exc}")

    import_total_ms = int((time.perf_counter() - import_started_at) * 1000)
    perf_record("import", "import_total", import_total_ms, metadata={"track_count": total})
    if perf_trace_enabled():
        try:
            from pathlib import Path

            from playlist_builder.reports.perf_report import write_perf_csv, write_perf_json

            perf_dir = Path("reports/perf")
            write_perf_json(perf_session, perf_dir, stem="import")
            write_perf_csv(perf_session, perf_dir, stem="import")
        except OSError as exc:
            _import_log(f"perf report write failed: {exc}")

    phase = _final_phase(aligned)
    import_state = track_add_results_to_import_state(playlist.name, aligned, phase=phase)
    yield ImportPlaylistResult(import_result=import_state)


def _prefill_resolved_outcomes_before_checkpoint(
    import_port,
    rows: list,
    start_index: int,
) -> list:
    """Rebuild resolution outcomes for tracks already resolved before a manual pause.

    On resume the main loop starts at ``checkpoint.next_index``; without this prefill
    ``deliver_playlist`` would receive a partial outcome list misaligned with the
    full playlist (see ``_flatten_playlist_with_outcomes``).
    """
    if start_index <= 0:
        return []
    prefix_rows = rows[:start_index]
    resolved_batch = import_port.resolve_batch(
        [(track, section_name) for track, section_name in prefix_rows]
    )
    return list(zip(resolved_batch, (section_name for _, section_name in prefix_rows), strict=True))


def _flatten_rows(playlist) -> list[tuple]:
    rows: list[tuple] = []
    for section in playlist.sections:
        for track in section.tracks:
            rows.append((track, section.name))
    return rows


def _final_phase(results: list[TrackAddResult]) -> ImportPhase:
    if not results:
        return ImportPhase.FAILED
    if all(item.status == TrackAddStatus.ERROR for item in results):
        return ImportPhase.FAILED
    if any(item.status in {TrackAddStatus.NOT_FOUND, TrackAddStatus.ERROR} for item in results):
        return ImportPhase.PARTIAL_SUCCESS
    return ImportPhase.COMPLETED
