from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackRef
from playlist_builder.planning.models import CandidateTrack, GeneratedPlaylist, PlaylistRequest, SeedTrack
from playlist_builder.ui.bridge import BridgeCommand, BridgeErrorCode, JsonRpcEngineBridge, process_json_line
from playlist_builder.app.bridge_runtime import RuntimeEngineBridgeBackend
from playlist_builder.app.bridge_runtime.manual_gate import ManualAcquisitionGate, ManualAcquisitionInterrupted
from playlist_builder.app.bridge_runtime.mapping import (
    generated_playlist_to_ui_result,
    track_add_results_to_import_state,
    ui_request_to_playlist_request,
)
from playlist_builder.ui.shared.dto import PlaylistGenerationRequest, SeedReference
from playlist_builder.ui.shared.dto.enums import EnergyCurveProfile, ImportPhase, ImportTrackStatus
from playlist_builder.ui.shared.dto.generation import EnergyCurveOption
from playlist_builder.ui.shared.validation import dto_to_dict


def test_ui_request_mapping_builds_playlist_request():
    request = PlaylistGenerationRequest(
        name="Pool Party",
        provider_id=ProviderId.APPLE_MUSIC,
        seeds=(SeedReference("Kygo", "Firestone"),),
        keywords=("tropical", "dance"),
        target_track_count=12,
        energy_curve=EnergyCurveOption(profile=EnergyCurveProfile.RISING),
    )
    playlist_request = ui_request_to_playlist_request(request)
    playlist_request.validate()
    assert playlist_request.name == "Pool Party"
    assert len(playlist_request.seeds) == 1
    assert playlist_request.constraints.target_track_count == 12


def test_ui_request_mapping_keywords_only_anchor_seed():
    request = PlaylistGenerationRequest(
        name="Keywords Only",
        provider_id=ProviderId.APPLE_MUSIC,
        keywords=("tropical",),
        target_track_count=8,
    )
    playlist_request = ui_request_to_playlist_request(request)
    assert len(playlist_request.seeds) == 1
    assert playlist_request.seeds[0].track.artist == "tropical"


def test_generated_playlist_to_ui_result_normalizes_scores():
    playlist_request = PlaylistRequest(
        name="Test",
        seeds=(SeedTrack(TrackRef("Kygo", "Firestone")),),
        constraints=__import__("playlist_builder.planning.models", fromlist=["GenerationConstraints"]).GenerationConstraints(
            target_track_count=1,
        ),
    )
    generated = GeneratedPlaylist(
        request=playlist_request,
        candidates=(
            CandidateTrack(
                track=TrackRef("Kygo", "Firestone"),
                score=92.0,
                source="seed",
            ),
        ),
    )
    result = generated_playlist_to_ui_result(generated, provider_id=ProviderId.APPLE_MUSIC)
    assert result.track_count == 1
    assert result.sections[0].tracks[0].score == pytest.approx(0.92)
    payload = json.dumps(dto_to_dict(result), ensure_ascii=False)
    assert "persistent_id" not in payload


def test_bridge_response_never_exposes_persistent_id():
    from playlist_builder.core.models import TrackAddResult, TrackAddStatus

    state = track_add_results_to_import_state(
        "Demo",
        [
            TrackAddResult(
                track=TrackRef("Kygo", "Firestone"),
                status=TrackAddStatus.ADDED,
            )
        ],
    )
    payload = json.dumps(dto_to_dict(state), ensure_ascii=False)
    assert "persistent_id" not in payload


def test_continue_manual_acquisition_command():
    from playlist_builder.ui.bridge.commands import ImportPlaylistResult
    from playlist_builder.ui.shared.dto.import_state import ImportResultState

    backend = MagicMock()
    final = ImportPlaylistResult(
        import_result=ImportResultState(playlist_name="Demo", phase=ImportPhase.COMPLETED),
    )
    backend.continue_manual_acquisition_stream.return_value = [final]
    bridge = JsonRpcEngineBridge(backend=backend)
    messages = bridge.handle(
        {
            "id": "resume-1",
            "command": BridgeCommand.CONTINUE_MANUAL_ACQUISITION.value,
            "params": {"import_session_id": "abc"},
        }
    )
    assert any(message.get("event") == "started" for message in messages)
    assert messages[-1]["ok"] is True
    assert messages[-1]["result"]["acknowledged"] is True


def test_probe_manual_acquisition_command():
    backend = MagicMock()
    backend.probe_manual_acquisition.return_value = {"found": True, "message": "ok"}
    bridge = JsonRpcEngineBridge(backend=backend)
    messages = bridge.handle(
        {
            "id": "probe-1",
            "command": BridgeCommand.PROBE_MANUAL_ACQUISITION.value,
            "params": {"import_session_id": "abc"},
        }
    )
    assert messages[-1]["ok"] is True
    assert messages[-1]["result"]["found"] is True


@patch("playlist_builder.app.bridge_runtime.backend.stream_import_playlist")
def test_runtime_backend_import_delegates_to_stream(mock_stream):
    from playlist_builder.app.factory import build_app_context

    final = __import__(
        "playlist_builder.ui.bridge.commands",
        fromlist=["ImportPlaylistResult"],
    ).ImportPlaylistResult(
        import_result=__import__(
            "playlist_builder.ui.shared.dto.import_state",
            fromlist=["ImportResultState"],
        ).ImportResultState(playlist_name="Demo", phase=ImportPhase.COMPLETED),
    )
    mock_stream.return_value = iter([final])
    backend = RuntimeEngineBridgeBackend(build_app_context())
    playlist = PlaylistDefinition(
        name="Demo",
        sections=(PlaylistSection(name="Main", tracks=(TrackRef("A", "B"),)),),
    )
    result = backend.import_playlist(playlist, sync=True, write_json_diagnostics=False)
    assert result.import_result.playlist_name == "Demo"


@patch("playlist_builder.app.bridge_runtime.backend.GenerationSessionEngine.generate")
def test_runtime_backend_generate_maps_engine_result(mock_generate):
    from playlist_builder.app.factory import build_app_context
    from playlist_builder.session.models import GenerationSession

    playlist_request = ui_request_to_playlist_request(
        PlaylistGenerationRequest(
            name="Pool",
            provider_id=ProviderId.APPLE_MUSIC,
            seeds=(SeedReference("Kygo", "Firestone"),),
            target_track_count=5,
        )
    )
    generated = GeneratedPlaylist(
        request=playlist_request,
        candidates=(
            CandidateTrack(track=TrackRef("Kygo", "Firestone"), score=90.0, source="seed"),
        ),
    )
    mock_generate.return_value = GenerationSession(
        request=playlist_request,
        discovery_result=MagicMock(),
        generated_playlist=generated,
        analysis=MagicMock(),
        report="",
    )
    backend = RuntimeEngineBridgeBackend(build_app_context())
    result = backend.generate_playlist(
        PlaylistGenerationRequest(
            name="Pool",
            provider_id=ProviderId.APPLE_MUSIC,
            seeds=(SeedReference("Kygo", "Firestone"),),
            target_track_count=5,
        )
    )
    assert result.result.playlist_name == "Pool"
    assert result.result.track_count == 1


def test_provider_unavailable_on_non_macos_import():
    from playlist_builder.app.factory import build_app_context
    from playlist_builder.app.bridge_runtime.import_stream import stream_import_playlist
    from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
    from playlist_builder.ui.bridge.errors import BridgeError

    playlist = PlaylistDefinition(
        name="Demo",
        sections=(PlaylistSection(name="Main", tracks=(TrackRef("A", "B"),)),),
    )
    with patch.object(sys, "platform", "linux"):
        with pytest.raises(BridgeError) as exc:
            list(
                stream_import_playlist(
                    build_app_context(),
                    playlist,
                    "req",
                    sync=True,
                    write_json_diagnostics=False,
                    session_store=ImportSessionStore(),
                )
            )
    assert exc.value.code == BridgeErrorCode.PROVIDER_UNAVAILABLE  # type: ignore[attr-defined]


def test_engine_bridge_cli_module_importable():
    from playlist_builder.cli import engine_bridge

    assert callable(engine_bridge.main)


def test_runtime_backend_diagnostics_includes_summary_and_events():
    from playlist_builder.app.factory import build_app_context

    backend = RuntimeEngineBridgeBackend(build_app_context())
    result = backend.diagnostics()
    payload = json.dumps(result.to_dict(), ensure_ascii=False)

    assert result.engine_version
    assert "summary" in payload
    assert result.summary["bridge_status"] == "connected"
    assert "catalog_cache_entries" in result.summary
    assert "identity_cache_entries" in result.summary
    assert isinstance(result.summary["active_providers"], list)
    assert len(result.events) >= 2
    assert "persistent_id" not in payload


def test_bridge_diagnostics_command_returns_enriched_payload():
    from playlist_builder.app.factory import build_app_context

    bridge = JsonRpcEngineBridge(backend=RuntimeEngineBridgeBackend(build_app_context()))
    messages = bridge.handle({"id": "diag-1", "command": BridgeCommand.DIAGNOSTICS.value, "params": {}})
    assert messages[-1]["ok"] is True
    result = messages[-1]["result"]
    assert "engine_version" in result
    assert "summary" in result
    assert result["summary"]["bridge_status"] == "connected"
    assert "events" in result
    payload = json.dumps(result, ensure_ascii=False)
    assert "persistent_id" not in payload
