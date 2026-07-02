from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol, runtime_checkable

from playlist_builder.core.models import PlaylistDefinition
from playlist_builder.ui.bridge.commands import (
    DiagnosticsResult,
    GeneratePlaylistResult,
    ImportPlaylistResult,
    ListProvidersResult,
    ValidateGenerationRequestResult,
)
from playlist_builder.ui.bridge.events import BridgeEvent
from playlist_builder.ui.shared.dto import (
    ImportResultState,
    PlaylistGenerationRequest,
    PlaylistGenerationResult,
    ProviderOption,
)


@runtime_checkable
class GenerationBackend(Protocol):
    def generate_playlist(self, request: PlaylistGenerationRequest) -> PlaylistGenerationResult: ...


@runtime_checkable
class ImportBackend(Protocol):
    def import_playlist(
        self,
        playlist: PlaylistDefinition,
        *,
        sync: bool = True,
        write_json_diagnostics: bool = True,
    ) -> Iterator[BridgeEvent]: ...


@runtime_checkable
class DiagnosticsBackend(Protocol):
    def diagnostics(self) -> DiagnosticsResult: ...


@runtime_checkable
class ProviderListingBackend(Protocol):
    def list_providers(self) -> tuple[ProviderOption, ...]: ...


@runtime_checkable
class EngineBridge(Protocol):
    """JSON command dispatcher between SwiftUI shells and the Python engine."""

    def handle(self, request: dict[str, Any]) -> list[dict[str, Any]]: ...


@runtime_checkable
class EngineBridgeBackend(Protocol):
    """Optional runtime adapters for commands that touch the engine."""

    def list_providers(self) -> ListProvidersResult: ...

    def generate_playlist(self, request: PlaylistGenerationRequest, request_id: str = "generate") -> GeneratePlaylistResult: ...

    def import_playlist(self, playlist: PlaylistDefinition, *, sync: bool, write_json_diagnostics: bool) -> ImportPlaylistResult: ...

    def import_playlist_stream(
        self,
        playlist: PlaylistDefinition,
        *,
        sync: bool,
        write_json_diagnostics: bool,
        request_id: str = "import",
        history_session_id: str | None = None,
    ) -> Iterator[BridgeEvent | ImportPlaylistResult]: ...

    def diagnostics(self) -> DiagnosticsResult: ...
