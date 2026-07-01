from __future__ import annotations

import sys
from collections.abc import Iterator

from playlist_builder import __version__
from playlist_builder.app.factory import AppContext
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.core.models import PlaylistDefinition
from playlist_builder.discovery.itunes_provider import ITunesCandidateProvider
from playlist_builder.discovery.pipeline import DiscoveryPipeline
from playlist_builder.discovery.providers import StaticCandidateProvider
from playlist_builder.session.engine import GenerationSessionEngine
from playlist_builder.ui.bridge.commands import (
    DiagnosticsResult,
    GeneratePlaylistResult,
    ImportPlaylistResult,
    ListProvidersResult,
)
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.ui.bridge.events import BridgeEvent
from playlist_builder.app.bridge_runtime.import_stream import stream_import_playlist
from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
from playlist_builder.app.bridge_runtime.mapping import (
    generated_playlist_to_ui_result,
    ui_request_to_playlist_request,
)
from playlist_builder.ui.shared.dto import PlaylistGenerationRequest, ProviderOption, default_provider_options


class RuntimeEngineBridgeBackend:
    """Production EngineBridgeBackend wiring generation and import use cases."""

    def __init__(self, context: AppContext, *, session_store: ImportSessionStore | None = None) -> None:
        self._context = context
        self._session_store = session_store or ImportSessionStore()
        self._generation_engine = self._build_generation_engine(context)

    def continue_manual_acquisition(self, params: dict) -> dict[str, object]:
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
        return {"acknowledged": True, "import": final.to_dict()["import"]}

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

    def generate_playlist(self, request: PlaylistGenerationRequest) -> GeneratePlaylistResult:
        playlist_request = ui_request_to_playlist_request(request)
        playlist_request.validate()
        try:
            session = self._generation_engine.generate(playlist_request)
        except ValueError as exc:
            raise BridgeError(BridgeErrorCode.VALIDATION_FAILED, str(exc)) from exc
        except Exception as exc:
            raise BridgeError(BridgeErrorCode.ENGINE_ERROR, str(exc)) from exc

        ui_result = generated_playlist_to_ui_result(session.generated_playlist, provider_id=request.provider_id)
        return GeneratePlaylistResult(result=ui_result)

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
    ) -> Iterator[BridgeEvent | ImportPlaylistResult]:
        del sync  # sync import only for MVP — incremental arrives later
        yield from stream_import_playlist(
            self._context,
            playlist,
            request_id=request_id,
            sync=True,
            write_json_diagnostics=write_json_diagnostics,
            session_store=self._session_store,
        )

    def diagnostics(self) -> DiagnosticsResult:
        return DiagnosticsResult(engine_version=__version__)

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
