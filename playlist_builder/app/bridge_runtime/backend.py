from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from playlist_builder import __version__
from playlist_builder.app.factory import AppContext
from playlist_builder.canonical.compat import canonical_playlist_from_legacy
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.core.models import PlaylistDefinition
from playlist_builder.discovery.itunes_provider import ITunesCandidateProvider
from playlist_builder.discovery.pipeline import DiscoveryPipeline
from playlist_builder.discovery.providers import StaticCandidateProvider
from playlist_builder.session.engine import GenerationSessionEngine
from playlist_builder.app.use_cases.autocomplete_search import AutocompleteSearchUseCase
from playlist_builder.ui.bridge.commands import (
    AutocompleteSearchResult,
    DiagnosticsResult,
    GeneratePlaylistResult,
    ImportPlaylistResult,
    ListProvidersResult,
    autocomplete_request_from_dict,
)
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.ui.bridge.events import BridgeEvent
from playlist_builder.app.bridge_runtime.diagnostics_snapshot import build_diagnostics_snapshot
from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
from playlist_builder.app.bridge_runtime.import_stream import stream_import_playlist
from playlist_builder.app.bridge_runtime.manual_acquisition_workflow import ManualAcquisitionWorkflowCoordinator
from playlist_builder.infrastructure.manual_continue_trace import log as manual_continue_trace
from playlist_builder.app.bridge_runtime.mapping import (
    generated_playlist_to_ui_result,
    ui_request_to_playlist_request,
)
from playlist_builder.ui.shared.dto import PlaylistGenerationRequest, ProviderOption, default_provider_options
from playlist_builder.ui.shared.history import (
    HistoryDiagnosticsSummary,
    SessionHistoryRepository,
    SessionHistoryService,
    record_to_dict,
)
from playlist_builder.infrastructure.perf import PerfSession, perf_record, perf_span, perf_trace_enabled
from playlist_builder.ui.shared.validation import dto_to_dict


class RuntimeEngineBridgeBackend:
    """Production EngineBridgeBackend wiring generation and import use cases."""

    def __init__(self, context: AppContext, *, session_store: ImportSessionStore | None = None) -> None:
        self._context = context
        self._session_store = session_store or ImportSessionStore()
        self._manual_workflow = ManualAcquisitionWorkflowCoordinator(
            context=context,
            session_store=self._session_store,
        )
        self._generation_engine = self._build_generation_engine(context)
        self._history = SessionHistoryService(SessionHistoryRepository(Path("data/history/sessions.json")))
        self._autocomplete = AutocompleteSearchUseCase(context.gateway)

    def autocomplete_search(self, params: dict) -> AutocompleteSearchResult:
        request = autocomplete_request_from_dict(params)
        response = self._autocomplete.search(request)
        return AutocompleteSearchResult(response=response)

    def continue_manual_acquisition(self, params: dict) -> dict[str, object]:
        final = self._continue_manual_acquisition_result(params)
        return {"acknowledged": True, "import": final.to_dict()["import"]}

    def continue_manual_acquisition_stream(
        self,
        params: dict,
    ) -> Iterator[BridgeEvent | ImportPlaylistResult]:
        session_id = str(params.get("import_session_id", "")).strip()
        manual_continue_trace(f"ENTER backend.continue_manual_acquisition_stream(session_id={session_id})")
        if not session_id:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "import_session_id est requis.")
        checkpoint = self._session_store.load(session_id)
        if checkpoint is None:
            manual_continue_trace("EXIT backend.continue_manual_acquisition_stream — checkpoint missing")
            raise BridgeError(
                BridgeErrorCode.MANUAL_ACTION_REQUIRED,
                "Session d'import introuvable ou expirée.",
            )
        manual_continue_trace(
            f"CALL backend.mark_resuming_import() checkpoint.next_index={checkpoint.next_index}"
        )
        self._manual_workflow.mark_resuming_import()
        manual_continue_trace("CALL stream_import_playlist(resume)")
        for item in stream_import_playlist(
            self._context,
            checkpoint.playlist,
            checkpoint.request_id,
            sync=checkpoint.sync,
            write_json_diagnostics=checkpoint.write_json_diagnostics,
            session_store=self._session_store,
            checkpoint=checkpoint,
        ):
            if isinstance(item, ImportPlaylistResult):
                manual_continue_trace("YIELD backend.continue_manual_acquisition_stream ImportPlaylistResult")
                yield self._attach_history_import_result(item, checkpoint.history_session_id)
                continue
            yield item
        manual_continue_trace("EXIT backend.continue_manual_acquisition_stream")

    def probe_manual_acquisition(self, params: dict) -> dict[str, object]:
        manual_continue_trace("ENTER backend.probe_manual_acquisition()")
        result = self._manual_workflow.probe_manual_acquisition(params)
        manual_continue_trace(
            f"RETURN backend.probe_manual_acquisition() found={result.get('found')} workflow_phase={result.get('workflow_phase')}"
        )
        return result

    def _continue_manual_acquisition_result(self, params: dict) -> ImportPlaylistResult:
        self._manual_workflow.mark_resuming_import()
        session_id = str(params.get("import_session_id", "")).strip()
        if not session_id:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "import_session_id est requis.")
        checkpoint = self._session_store.load(session_id)
        if checkpoint is None:
            raise BridgeError(
                BridgeErrorCode.MANUAL_ACTION_REQUIRED,
                "Session d'import introuvable ou expirée.",
            )
        final: ImportPlaylistResult | None = None
        for item in stream_import_playlist(
            self._context,
            checkpoint.playlist,
            checkpoint.request_id,
            sync=checkpoint.sync,
            write_json_diagnostics=checkpoint.write_json_diagnostics,
            session_store=self._session_store,
            checkpoint=checkpoint,
        ):
            if isinstance(item, ImportPlaylistResult):
                final = item
        if final is None:
            raise BridgeError(BridgeErrorCode.ENGINE_ERROR, "Reprise d'import sans résultat.")
        return final

    def list_providers(self) -> ListProvidersResult:
        providers: list[ProviderOption] = []
        for option in default_provider_options():
            if option.provider_id == ProviderId.APPLE_MUSIC and sys.platform != "darwin":
                providers.append(
                    ProviderOption(
                        provider_id=option.provider_id,
                        display_name=option.display_name,
                        is_available=False,
                        is_connected=False,
                        capabilities=option.capabilities,
                        unavailable_reason="Import Apple Music disponible uniquement sur macOS.",
                    )
                )
                continue
            providers.append(option)
        return ListProvidersResult(providers=tuple(providers))

    def generate_playlist(self, request: PlaylistGenerationRequest, request_id: str = "generate") -> GeneratePlaylistResult:
        playlist_request = ui_request_to_playlist_request(request)
        playlist_request.validate()
        target_count = playlist_request.constraints.target_track_count
        with PerfSession(
            scenario="generate",
            operation="generate_playlist",
            track_count=target_count,
        ) as perf_session:
            try:
                with perf_span("generate", "engine_generate", metadata={"target_track_count": target_count}):
                    session = self._generation_engine.generate(playlist_request)
            except ValueError as exc:
                raise BridgeError(BridgeErrorCode.VALIDATION_FAILED, str(exc)) from exc
            except Exception as exc:
                raise BridgeError(BridgeErrorCode.ENGINE_ERROR, str(exc)) from exc

            shortfall_count = max(0, target_count - len(session.generated_playlist.candidates))
            perf_record(
                "generate",
                "generate_total",
                perf_session.total_duration_ms,
                metadata={
                    "track_count": len(session.generated_playlist.candidates),
                    "shortfall_count": shortfall_count,
                },
            )
            if perf_trace_enabled():
                try:
                    from playlist_builder.reports.perf_report import write_perf_csv, write_perf_json

                    write_perf_json(perf_session, Path("reports/perf"), stem="generate")
                    write_perf_csv(perf_session, Path("reports/perf"), stem="generate")
                except OSError:
                    pass

        ui_result = generated_playlist_to_ui_result(session.generated_playlist, provider_id=request.provider_id)
        history = self._history.create_generation_session(
            request_id=request_id,
            playlist_name=ui_result.playlist_name,
            provider_id=request.provider_id,
            generation_request=dto_to_dict(request),
            generation_result=dto_to_dict(ui_result),
            track_count=ui_result.track_count,
        )
        return GeneratePlaylistResult(result=ui_result, history_session_id=history.session_id)

    def import_playlist(
        self,
        playlist: PlaylistDefinition,
        *,
        sync: bool,
        write_json_diagnostics: bool,
    ) -> ImportPlaylistResult:
        final: ImportPlaylistResult | None = None
        for item in self.import_playlist_stream(
            playlist,
            sync=sync,
            write_json_diagnostics=write_json_diagnostics,
        ):
            if isinstance(item, ImportPlaylistResult):
                final = item
        if final is None:
            raise BridgeError(BridgeErrorCode.ENGINE_ERROR, "Import terminé sans résultat.")
        return final

    def import_playlist_stream(
        self,
        playlist: PlaylistDefinition,
        *,
        sync: bool,
        write_json_diagnostics: bool,
        request_id: str = "import",
        history_session_id: str | None = None,
    ) -> Iterator[BridgeEvent | ImportPlaylistResult]:
        del sync  # sync import only for MVP — incremental arrives later
        for item in stream_import_playlist(
            self._context,
            playlist,
            request_id=request_id,
            sync=True,
            write_json_diagnostics=write_json_diagnostics,
            session_store=self._session_store,
            history_session_id=history_session_id or "",
        ):
            if isinstance(item, ImportPlaylistResult):
                yield self._attach_history_import_result(item, history_session_id)
                continue
            yield item

    def diagnostics(self) -> DiagnosticsResult:
        providers = self.list_providers().providers
        summary, events = build_diagnostics_snapshot(self._context, providers=providers)
        summary["recent_history_sessions"] = [record_to_dict(item) for item in self._history.list_sessions()[:5]]
        return DiagnosticsResult(engine_version=__version__, summary=summary, events=events)

    def list_history(self) -> tuple[dict[str, Any], ...]:
        return tuple(record_to_dict(item) for item in self._history.list_sessions())

    def get_history_session(self, session_id: str) -> dict[str, Any] | None:
        session = self._history.get_session(session_id)
        if session is None:
            return None
        return record_to_dict(session)

    def delete_history_session(self, session_id: str) -> bool:
        return self._history.delete_session(session_id)

    def clear_history(self) -> bool:
        self._history.clear()
        return True

    def export_history_session(self, session_id: str) -> dict[str, Any] | None:
        return self._history.export_session(session_id)

    def retry_import_tracks_stream(
        self,
        playlist: PlaylistDefinition,
        *,
        track_indices: list[int],
        existing_results: list | None = None,
        request_id: str = "retry_import",
        history_session_id: str | None = None,
    ) -> Iterator[BridgeEvent | ImportPlaylistResult]:
        from playlist_builder.app.bridge_runtime.retry_import import stream_retry_import_tracks

        for item in stream_retry_import_tracks(
            self._context,
            playlist,
            request_id,
            track_indices=track_indices,
            existing_results=existing_results,
        ):
            if isinstance(item, ImportPlaylistResult):
                yield self._attach_history_import_result(item, history_session_id)
            else:
                yield item

    def replay_generation(self, session_id: str, request_id: str = "replay") -> GeneratePlaylistResult:
        payload = self._history.export_session(session_id)
        if payload is None:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "Session historique introuvable.")
        request_payload = payload.get("generation_request")
        if not isinstance(request_payload, dict):
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "Session sans requête de génération.")
        from playlist_builder.ui.bridge.commands import playlist_generation_request_from_dict

        request = playlist_generation_request_from_dict(request_payload)
        return self.generate_playlist(request, request_id=request_id)

    def _attach_history_import_result(
        self,
        item: ImportPlaylistResult,
        history_session_id: str | None,
    ) -> ImportPlaylistResult:
        diagnostics = HistoryDiagnosticsSummary()
        if item.import_result.phase.value == "failed":
            diagnostics = HistoryDiagnosticsSummary(errors=1, last_message="Import failed")
        updated = self._history.attach_import_result(
            session_id=history_session_id,
            playlist_name=item.import_result.playlist_name,
            provider_id=ProviderId.APPLE_MUSIC,
            result=item.import_result,
            diagnostics=diagnostics,
        )
        if item.import_result.phase.value != "waiting_for_manual_acquisition":
            self._session_store.delete(item.import_result.import_session_id)
        return ImportPlaylistResult(import_result=item.import_result, history_session_id=updated.session_id)

    def list_managed_playlists(self) -> tuple[dict[str, Any], ...]:
        from playlist_builder.app.bridge_runtime.playlist_library import list_managed_playlists_from_history

        return list_managed_playlists_from_history(self.list_history())

    def get_managed_playlist(self, local_playlist_id: str) -> dict[str, Any] | None:
        from playlist_builder.app.bridge_runtime.playlist_library import managed_playlist_detail

        return managed_playlist_detail(self, local_playlist_id)

    def sync_managed_playlist(self, params: dict[str, Any]) -> dict[str, Any]:
        from playlist_builder.app.bridge_runtime.playlist_library import sync_managed_playlist_stub

        return sync_managed_playlist_stub(params)

    def plan_sync(self, params: dict[str, Any]) -> dict[str, Any]:
        from playlist_builder.app.bridge_runtime.playlist_library import managed_playlist_detail
        from playlist_builder.app.bridge_runtime.playlist_sync_plan import (
            managed_playlist_detail_from_dict,
            plan_sync,
            remote_snapshot_from_dict,
        )
        from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode

        provider_raw = params.get("provider_id", ProviderId.APPLE_MUSIC.value)
        try:
            provider_id = ProviderId(str(provider_raw))
        except ValueError as exc:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"provider_id invalide : {provider_raw!r}") from exc

        direction_raw = str(params.get("direction", SyncDirection.PULL_FROM_PROVIDER.value))
        try:
            direction = SyncDirection(direction_raw)
        except ValueError as exc:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"direction invalide : {direction_raw!r}") from exc

        mode_raw = str(params.get("sync_mode", SyncMode.DRY_RUN.value))
        try:
            sync_mode = SyncMode(mode_raw)
        except ValueError as exc:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"sync_mode invalide : {mode_raw!r}") from exc

        remote_snapshot = None
        if isinstance(params.get("remote_playlist"), dict):
            remote_snapshot = remote_snapshot_from_dict({"remote_playlist": params["remote_playlist"]})

        local_detail = None
        if isinstance(params.get("local_playlist"), dict):
            local_detail = managed_playlist_detail_from_dict({"playlist": params["local_playlist"]})
        else:
            local_playlist_id = str(params.get("local_playlist_id", "")).strip()
            if not local_playlist_id:
                raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "local_playlist_id est requis.")
            playlist_payload = managed_playlist_detail(self, local_playlist_id)
            if playlist_payload is None:
                raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "Playlist locale introuvable.")
            local_detail = managed_playlist_detail_from_dict(playlist_payload)

        remote_playlist_id = str(params.get("remote_playlist_id", "")).strip() or None
        return plan_sync(
            self._context.registry,
            local_detail=local_detail,
            remote_snapshot=remote_snapshot,
            provider_id=provider_id,
            direction=direction,
            sync_mode=sync_mode,
            remote_playlist_id=remote_playlist_id,
        )

    def list_remote_playlists(self, params: dict[str, Any]) -> dict[str, Any]:
        from playlist_builder.app.bridge_runtime.remote_playlist import list_remote_playlists

        provider_raw = params.get("provider_id", ProviderId.APPLE_MUSIC.value)
        try:
            provider_id = ProviderId(str(provider_raw))
        except ValueError as exc:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"provider_id invalide : {provider_raw!r}") from exc
        account_id = str(params.get("account_id", "")).strip() or None
        playlists = list_remote_playlists(
            self._context.registry,
            provider_id=provider_id,
            account_id=account_id,
        )
        return {"remote_playlists": list(playlists)}

    def get_remote_playlist(self, params: dict[str, Any]) -> dict[str, Any]:
        from playlist_builder.app.bridge_runtime.remote_playlist import get_remote_playlist

        provider_raw = params.get("provider_id", ProviderId.APPLE_MUSIC.value)
        try:
            provider_id = ProviderId(str(provider_raw))
        except ValueError as exc:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, f"provider_id invalide : {provider_raw!r}") from exc
        remote_playlist_id = str(params.get("remote_playlist_id", "")).strip()
        snapshot = get_remote_playlist(
            self._context.registry,
            provider_id=provider_id,
            remote_playlist_id=remote_playlist_id,
        )
        return {"remote_playlist": snapshot}

    @staticmethod
    def _build_generation_engine(context: AppContext) -> GenerationSessionEngine:
        settings = context.settings
        if settings.use_catalog_cache:
            cache = JsonCache(settings.catalog_cache_path)
        else:
            cache = None
        apple_gateway = context.registry.get(ProviderId.APPLE_MUSIC)
        if apple_gateway is None or apple_gateway.catalog is None:
            return GenerationSessionEngine(DiscoveryPipeline([StaticCandidateProvider([])]))

        provider = ITunesCandidateProvider(apple_gateway.catalog, country_code=settings.country_code)
        return GenerationSessionEngine(DiscoveryPipeline([provider]))
