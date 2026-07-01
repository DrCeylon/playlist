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
from playlist_builder.ui.bridge.events import BridgeEvent, diagnostic_event, manual_acquisition_required_event, progress_event
from playlist_builder.app.bridge_runtime.import_session import ImportSessionCheckpoint, ImportSessionStore, new_session_id
from playlist_builder.app.bridge_runtime.manual_gate import ManualAcquisitionInterrupted
from playlist_builder.app.bridge_runtime.mapping import track_add_results_to_import_state
from playlist_builder.ui.shared.dto.enums import ImportPhase


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
    yield progress_event(
        request_id,
        phase=ImportPhase.RESOLVING.value,
        processed_tracks=start_index,
        total_tracks=total,
        playlist_name=playlist.name,
        import_session_id=session_id,
    )

    outcomes: list = []
    for index in range(total):
        track, section_name = rows[index]
        label = f"{track.artist.display_name} — {track.title}"
        if checkpoint is not None and index < start_index:
            outcomes.append((resolver.resolve(track, section=section_name), section_name))
            continue
        yield progress_event(
            request_id,
            phase=ImportPhase.RESOLVING.value,
            processed_tracks=index,
            total_tracks=total,
            current_track_label=label,
            import_session_id=session_id,
        )
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
                import_session_id=session_id,
            )
            from playlist_builder.ui.shared.dto.import_state import ImportResultState, ImportTrackOutcome
            from playlist_builder.ui.shared.dto.enums import ImportTrackStatus

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

        if outcome.cache_hit:
            yield diagnostic_event(
                request_id,
                phase="cache_hit",
                message=f"Cache IdentityCache : {label}",
                artist=track.artist.display_name,
                title=track.title,
            )
        elif outcome.catalog_acquired:
            yield diagnostic_event(
                request_id,
                phase="catalog_lookup",
                message=f"Acquisition catalogue : {label}",
                artist=track.artist.display_name,
                title=track.title,
            )
        elif outcome.status == AppleMusicResolutionStatus.NOT_FOUND:
            yield diagnostic_event(
                request_id,
                phase="catalog_lookup",
                message=outcome.error or f"Introuvable : {label}",
                artist=track.artist.display_name,
                title=track.title,
            )
        outcomes.append((outcome, section_name))

    yield progress_event(
        request_id,
        phase=ImportPhase.DELIVERING.value,
        processed_tracks=total,
        total_tracks=total,
        playlist_name=playlist.name,
        import_session_id=session_id,
    )

    try:
        import_service.delivery.ensure_playlist(playlist.name)
        report = import_service.delivery.sync_playlist(canonical, [item[0] for item in outcomes])
    except RuntimeError as exc:
        raise BridgeError(BridgeErrorCode.PROVIDER_UNAVAILABLE, str(exc)) from exc

    aligned = track_results_aligned_with_playlist(playlist.tracks, report)
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
