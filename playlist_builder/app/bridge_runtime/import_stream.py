from __future__ import annotations

from collections.abc import Iterator

from playlist_builder.app.factory import AppContext
from playlist_builder.canonical.compat import canonical_playlist_from_legacy
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.core.models import PlaylistDefinition, TrackAddResult, TrackAddStatus
from playlist_builder.integration.apple_music.resolver import AppleMusicResolutionStatus
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
from playlist_builder.app.bridge_runtime.import_session import ImportSessionCheckpoint, ImportSessionStore, new_session_id
from playlist_builder.app.bridge_runtime.manual_gate import ManualAcquisitionInterrupted
from playlist_builder.app.bridge_runtime.mapping import track_add_results_to_import_state
from playlist_builder.ui.shared.dto.enums import ImportPhase, ImportTrackStatus


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


def stream_import_playlist(
    context: AppContext,
    playlist: PlaylistDefinition,
    request_id: str,
    *,
    sync: bool,
    write_json_diagnostics: bool,
    session_store: ImportSessionStore,
    checkpoint: ImportSessionCheckpoint | None = None,
) -> Iterator[BridgeEvent | ImportPlaylistResult]:
    import sys

    if sys.platform != "darwin":
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            "L'import Apple Music nécessite macOS.",
        )

    apple_gateway = context.registry.get(ProviderId.APPLE_MUSIC)
    if apple_gateway is None:
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            "Le fournisseur Apple Music n'est pas disponible.",
        )

    import_service = apple_gateway.import_service
    resolver = import_service.resolver
    applescript = resolver._applescript  # noqa: SLF001

    if context.settings.wait_for_manual_catalog_add:
        from playlist_builder.app.bridge_runtime.manual_gate import ManualAcquisitionGate

        resolver._manual_acquisition_hook = ManualAcquisitionGate().hook  # noqa: SLF001
    if checkpoint is not None:
        playlist = checkpoint.playlist
        request_id = checkpoint.request_id
        sync = checkpoint.sync
        write_json_diagnostics = checkpoint.write_json_diagnostics
        start_index = checkpoint.next_index
        session_id = checkpoint.session_id
    else:
        start_index = 0
        session_id = new_session_id()

    canonical = canonical_playlist_from_legacy(playlist)
    rows = _flatten_rows(canonical)
    total = len(rows)

    yield diagnostic_event(
        request_id,
        phase="import_start",
        message=f"Commande import_playlist reçue — {total} morceau(x) à traiter",
    )
    _import_log(f"playlist={playlist.name!r} tracks={total} history_session pending")
    yield diagnostic_event(
        request_id,
        phase="music_app",
        message="Connexion à Music.app via AppleScript…",
    )
    _import_log("Music.app ensure_running")
    try:
        applescript.ensure_running()
    except RuntimeError as exc:
        _import_log(f"Music.app ensure_running failed: {exc}")
        raise BridgeError(BridgeErrorCode.PROVIDER_UNAVAILABLE, str(exc)) from exc
    _import_log("Music.app ensure_running OK")
    yield diagnostic_event(
        request_id,
        phase="music_app",
        message="Music.app accessible",
    )

    yield progress_event(
        request_id,
        phase=ImportPhase.RESOLVING.value,
        processed_tracks=start_index,
        total_tracks=total,
        playlist_name=playlist.name,
        import_session_id=session_id,
    )

    outcomes: list = []
    added_count = 0
    skipped_count = 0
    not_found_count = 0
    error_count = 0
    for index in range(total):
        track, section_name = rows[index]
        artist_name = track.artist.display_name
        title_name = track.title
        label = f"{artist_name} — {title_name}"
        if checkpoint is not None and index < start_index:
            outcomes.append((resolver.resolve(track, section=section_name), section_name))
            continue
        yield _emit_track_progress(
            request_id,
            track_index=index,
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
        yield progress_event(
            request_id,
            phase=ImportPhase.RESOLVING.value,
            processed_tracks=index,
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
            track_index=index,
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
        _import_log(f"resolve {index + 1}/{total}: {label}")
        try:
            outcome = resolver.resolve(track, section=section_name)
        except ManualAcquisitionInterrupted as pause:
            session_store.save(
                ImportSessionCheckpoint(
                    session_id=session_id,
                    playlist=playlist,
                    next_index=index,
                    request_id=request_id,
                    sync=sync,
                    write_json_diagnostics=write_json_diagnostics,
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
                track_index=index,
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
            )
            yield ImportPlaylistResult(import_result=import_state)
            return

        track_status = ImportTrackStatus.PENDING
        track_message = "Résolu"
        if outcome.status == AppleMusicResolutionStatus.NOT_FOUND:
            not_found_count += 1
            track_status = ImportTrackStatus.NOT_FOUND
            track_message = outcome.error or "Introuvable dans Apple Music"
        elif outcome.status == AppleMusicResolutionStatus.ERROR:
            error_count += 1
            track_status = ImportTrackStatus.ERROR
            track_message = outcome.error or "Erreur de résolution"
        elif outcome.cache_hit:
            track_message = "Trouvé (cache)"
        elif outcome.catalog_acquired:
            yield _emit_track_progress(
                request_id,
                track_index=index,
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
            track_index=index,
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
        elif outcome.status == AppleMusicResolutionStatus.NOT_FOUND:
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
            processed_tracks=index + 1,
            total_tracks=total,
            current_track_label=label,
            import_session_id=session_id,
            added_count=added_count,
            skipped_count=skipped_count,
            not_found_count=not_found_count,
            error_count=error_count,
        )

    yield progress_event(
        request_id,
        phase=ImportPhase.DELIVERING.value,
        processed_tracks=total,
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
        message=f"Création/synchronisation de la playlist « {playlist.name} » dans Music.app…",
    )
    _import_log(f"ensure_playlist name={playlist.name!r}")

    try:
        import_service.delivery.ensure_playlist(playlist.name)
        _import_log("sync_playlist starting")
        report = import_service.delivery.sync_playlist(canonical, [item[0] for item in outcomes])
        _import_log("sync_playlist finished")
    except RuntimeError as exc:
        _import_log(f"delivery failed: {exc}")
        raise BridgeError(BridgeErrorCode.PROVIDER_UNAVAILABLE, str(exc)) from exc

    yield diagnostic_event(
        request_id,
        phase="delivering",
        message="Playlist synchronisée dans Music.app",
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
            message=f"Confirmation Music.app : {added_count} morceau(x) visible(s) dans la playlist",
        )
    if write_json_diagnostics:
        from pathlib import Path

        from playlist_builder.reports.import_diagnostics import write_import_diagnostics
        from playlist_builder.reports.playlist import write_playlist_report

        write_playlist_report(playlist.name, aligned, Path("reports"))
        write_import_diagnostics(playlist.name, report, aligned, Path("reports"))

    context.gateway.flush_caches(flush_catalog_cache=context.settings.use_catalog_cache)
    session_store.delete(session_id)
    phase = _final_phase(aligned)
    import_state = track_add_results_to_import_state(playlist.name, aligned, phase=phase)
    yield ImportPlaylistResult(import_result=import_state)


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
