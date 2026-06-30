from __future__ import annotations

import json
from collections.abc import Iterator

import pytest

from playlist_builder.core.models import PlaylistDefinition, PlaylistSection
from playlist_builder.ui.bridge import BridgeCommand, BridgeErrorCode, JsonRpcEngineBridge, process_json_line
from playlist_builder.ui.bridge.commands import (
    DiagnosticsResult,
    GeneratePlaylistResult,
    ImportPlaylistResult,
    ListProvidersResult,
)
from playlist_builder.ui.bridge.events import BridgeEvent, BridgeEventType, diagnostic_event, progress_event
from playlist_builder.ui.bridge.protocol import EngineBridgeBackend
from playlist_builder.ui.shared.dto import (
    GeneratedSectionPreview,
    GeneratedTrackPreview,
    ImportPhase,
    ImportResultState,
    ImportTrackOutcome,
    ImportTrackStatus,
    PlaylistGenerationRequest,
    PlaylistGenerationResult,
    ProviderOption,
    SeedReference,
)
from playlist_builder.canonical.enums import ConfidenceLevel, ProviderId


class FakeBackend(EngineBridgeBackend):
    def list_providers(self) -> ListProvidersResult:
        return ListProvidersResult(
            providers=(
                ProviderOption(
                    provider_id=ProviderId.APPLE_MUSIC,
                    display_name="Apple Music",
                    is_available=True,
                    is_connected=True,
                ),
            )
        )

    def generate_playlist(self, request: PlaylistGenerationRequest) -> GeneratePlaylistResult:
        return GeneratePlaylistResult(
            result=PlaylistGenerationResult(
                playlist_name=request.name,
                sections=(
                    GeneratedSectionPreview(
                        name="Main",
                        tracks=(
                            GeneratedTrackPreview(
                                "Kygo",
                                "Firestone",
                                "Main",
                                95.0,
                                ConfidenceLevel.HIGH,
                            ),
                        ),
                    ),
                ),
                average_score=95.0,
                provider_id=request.provider_id,
            )
        )

    def import_playlist(self, playlist: PlaylistDefinition, *, sync: bool, write_json_diagnostics: bool) -> ImportPlaylistResult:
        return ImportPlaylistResult(
            import_result=ImportResultState(
                playlist_name=playlist.name,
                outcomes=(
                    ImportTrackOutcome("Kygo", "Firestone", "Main", ImportTrackStatus.ADDED),
                ),
                phase=ImportPhase.COMPLETED,
            )
        )

    def import_playlist_stream(
        self,
        playlist: PlaylistDefinition,
        *,
        sync: bool,
        write_json_diagnostics: bool,
    ) -> Iterator[BridgeEvent | ImportPlaylistResult]:
        yield progress_event("req-import", processed_tracks=1, total_tracks=1)
        yield diagnostic_event("req-import", phase="gateway", message="import started")
        yield self.import_playlist(playlist, sync=sync, write_json_diagnostics=write_json_diagnostics)

    def diagnostics(self) -> DiagnosticsResult:
        return DiagnosticsResult(engine_version="9.9.9", events=())


def _generation_request_payload() -> dict:
    return {
        "name": "Pool Party",
        "provider_id": "apple_music",
        "seeds": [{"artist": "Kygo", "title": "Firestone"}],
        "target_track_count": 10,
        "energy_curve": {"profile": "rising"},
    }


def test_list_providers_command():
    bridge = JsonRpcEngineBridge()
    messages = bridge.handle({"id": "1", "command": BridgeCommand.LIST_PROVIDERS.value, "params": {}})
    assert messages[-1]["ok"] is True
    assert any(provider["is_available"] for provider in messages[-1]["result"]["providers"])


def test_unknown_command_returns_error():
    bridge = JsonRpcEngineBridge()
    messages = bridge.handle({"id": "x", "command": "unknown", "params": {}})
    assert messages[-1]["ok"] is False
    assert messages[-1]["error"]["code"] == BridgeErrorCode.INVALID_REQUEST.value
    assert "Unknown bridge command" in messages[-1]["error"]["message"]


def test_validate_generation_request_ok():
    bridge = JsonRpcEngineBridge()
    messages = bridge.handle(
        {
            "id": "2",
            "command": BridgeCommand.VALIDATE_GENERATION_REQUEST.value,
            "params": {"request": _generation_request_payload()},
        }
    )
    assert messages[-1]["ok"] is True
    assert messages[-1]["result"]["valid"] is True


def test_validate_generation_request_invalid():
    bridge = JsonRpcEngineBridge()
    messages = bridge.handle(
        {
            "id": "3",
            "command": BridgeCommand.VALIDATE_GENERATION_REQUEST.value,
            "params": {"request": {"name": "", "provider_id": "apple_music"}},
        }
    )
    assert messages[-1]["ok"] is True
    assert messages[-1]["result"]["valid"] is False
    assert messages[-1]["result"]["errors"]


def test_generate_playlist_requires_backend():
    bridge = JsonRpcEngineBridge()
    messages = bridge.handle(
        {
            "id": "4",
            "command": BridgeCommand.GENERATE_PLAYLIST.value,
            "params": {"request": _generation_request_payload()},
        }
    )
    assert messages[-1]["ok"] is False
    assert messages[-1]["error"]["code"] == BridgeErrorCode.NOT_CONFIGURED.value


def test_generate_playlist_with_mock_backend():
    bridge = JsonRpcEngineBridge(backend=FakeBackend())
    messages = bridge.handle(
        {
            "id": "5",
            "command": BridgeCommand.GENERATE_PLAYLIST.value,
            "params": {"request": _generation_request_payload()},
        }
    )
    assert messages[0]["type"] == "event"
    assert messages[0]["event"] == BridgeEventType.STARTED.value
    assert messages[-1]["ok"] is True
    assert messages[-1]["result"]["generation"]["playlist_name"] == "Pool Party"


def test_import_playlist_stream_events_and_result():
    bridge = JsonRpcEngineBridge(backend=FakeBackend())
    messages = bridge.handle(
        {
            "id": "req-import",
            "command": BridgeCommand.IMPORT_PLAYLIST.value,
            "params": {
                "playlist": {
                    "name": "E2E Test",
                    "sections": [
                        {
                            "name": "Main",
                            "songs": [{"artist": "Kygo", "title": "Firestone"}],
                        }
                    ],
                }
            },
        }
    )
    event_types = [message["event"] for message in messages if message.get("type") == "event"]
    assert BridgeEventType.STARTED.value in event_types
    assert BridgeEventType.PROGRESS.value in event_types
    assert BridgeEventType.DIAGNOSTIC.value in event_types
    assert BridgeEventType.COMPLETED.value in event_types
    assert messages[-1]["ok"] is True
    outcomes = messages[-1]["result"]["import"]["outcomes"]
    assert len(outcomes) == 1
    assert outcomes[0]["status"] == ImportTrackStatus.ADDED.value


def test_diagnostics_default_engine_version():
    bridge = JsonRpcEngineBridge()
    messages = bridge.handle({"id": "6", "command": BridgeCommand.DIAGNOSTICS.value, "params": {}})
    assert messages[-1]["ok"] is True
    assert "engine_version" in messages[-1]["result"]


def test_process_json_line_round_trip():
    bridge = JsonRpcEngineBridge()
    lines = process_json_line(
        bridge,
        json.dumps({"id": "7", "command": BridgeCommand.LIST_PROVIDERS.value, "params": {}}),
    )
    payload = json.loads(lines[-1])
    assert payload["ok"] is True


def test_generate_playlist_validation_failed():
    bridge = JsonRpcEngineBridge(backend=FakeBackend())
    messages = bridge.handle(
        {
            "id": "8",
            "command": BridgeCommand.GENERATE_PLAYLIST.value,
            "params": {"request": {"name": "", "provider_id": "apple_music"}},
        }
    )
    assert messages[-1]["ok"] is False
    assert messages[-1]["error"]["code"] == BridgeErrorCode.VALIDATION_FAILED.value


def test_generate_playlist_invalid_provider_is_invalid_request():
    bridge = JsonRpcEngineBridge(backend=FakeBackend())
    messages = bridge.handle(
        {
            "id": "9",
            "command": BridgeCommand.GENERATE_PLAYLIST.value,
            "params": {
                "request": {
                    "name": "Pool",
                    "provider_id": "not_a_provider",
                    "seeds": [{"artist": "Kygo", "title": "Firestone"}],
                    "target_track_count": 1,
                }
            },
        }
    )
    assert messages[-1]["ok"] is False
    assert messages[-1]["error"]["code"] == BridgeErrorCode.INVALID_REQUEST.value


def test_generate_playlist_backend_exception_is_engine_error():
    class BrokenBackend(FakeBackend):
        def generate_playlist(self, request):
            raise RuntimeError("backend exploded")

    bridge = JsonRpcEngineBridge(backend=BrokenBackend())
    messages = bridge.handle(
        {
            "id": "10",
            "command": BridgeCommand.GENERATE_PLAYLIST.value,
            "params": {"request": _generation_request_payload()},
        }
    )
    assert messages[-1]["ok"] is False
    assert messages[-1]["error"]["code"] == BridgeErrorCode.ENGINE_ERROR.value
    assert "backend exploded" in messages[-1]["error"]["message"]


def test_validate_generation_request_invalid_payload_is_invalid_request():
    bridge = JsonRpcEngineBridge()
    messages = bridge.handle(
        {
            "id": "11",
            "command": BridgeCommand.VALIDATE_GENERATION_REQUEST.value,
            "params": {"request": {"provider_id": "bad_provider"}},
        }
    )
    assert messages[-1]["ok"] is False
    assert messages[-1]["error"]["code"] == BridgeErrorCode.INVALID_REQUEST.value
