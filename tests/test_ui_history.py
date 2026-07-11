from __future__ import annotations

import json
from pathlib import Path

import pytest

from playlist_builder.app.bridge_runtime import RuntimeEngineBridgeBackend
from playlist_builder.app.factory import build_app_context
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.bridge import BridgeCommand, JsonRpcEngineBridge
from playlist_builder.ui.shared.dto import (
    ImportPhase,
    ImportResultState,
    ImportTrackOutcome,
    ImportTrackStatus,
    PlaylistGenerationRequest,
)
from playlist_builder.ui.shared.history import (
    SCHEMA_VERSION,
    HistoryDiagnosticsSummary,
    HistorySessionStatus,
    SessionHistoryRecord,
    SessionHistoryRepository,
    SessionHistoryService,
    record_from_dict,
    record_to_dict,
)


def _repo(tmp_path: Path) -> SessionHistoryRepository:
    return SessionHistoryRepository(tmp_path / "data" / "history" / "sessions.json")


def _sample_record() -> SessionHistoryRecord:
    return SessionHistoryRecord(
        session_id="hist-1",
        started_at_iso="2026-07-02T08:00:00",
        finished_at_iso="2026-07-02T08:00:05",
        playlist_name="Pool Party",
        provider_id=ProviderId.APPLE_MUSIC,
        status=HistorySessionStatus.GENERATED,
        track_count=12,
        added_count=0,
        skipped_count=0,
        not_found_count=0,
        error_count=0,
        duration_ms=5000,
        generation_request={"name": "Pool Party", "persistent_id": "never"},
    )


def test_history_create_and_list(tmp_path: Path):
    repository = _repo(tmp_path)
    service = SessionHistoryService(repository)
    created = service.create_generation_session(
        request_id="gen-1",
        playlist_name="Demo",
        provider_id=ProviderId.APPLE_MUSIC,
        generation_request={"name": "Demo"},
        generation_result={"playlist_name": "Demo"},
        track_count=1,
    )
    listed = service.list_sessions()
    assert listed
    assert listed[0].session_id == created.session_id


def test_history_update_session_import(tmp_path: Path):
    repository = _repo(tmp_path)
    service = SessionHistoryService(repository)
    created = service.create_generation_session(
        request_id="gen-2",
        playlist_name="Demo Import",
        provider_id=ProviderId.APPLE_MUSIC,
        generation_request={"name": "Demo Import"},
        generation_result={"playlist_name": "Demo Import"},
        track_count=2,
    )
    updated = service.attach_import_result(
        session_id=created.session_id,
        playlist_name="Demo Import",
        provider_id=created.provider_id,
        result=ImportResultState(
            playlist_name="Demo Import",
            phase=ImportPhase.COMPLETED,
            outcomes=(ImportTrackOutcome("A", "B", "Main", ImportTrackStatus.ADDED),),
        ),
        diagnostics=HistoryDiagnosticsSummary(warnings=1, errors=0, last_message="ok"),
    )
    assert updated.added_count == 1
    assert updated.status == HistorySessionStatus.IMPORTED


def test_history_get_delete_clear(tmp_path: Path):
    repository = _repo(tmp_path)
    record = _sample_record()
    repository.upsert(record)
    assert repository.get_session(record.session_id) is not None
    assert repository.delete_session(record.session_id) is True
    assert repository.get_session(record.session_id) is None
    repository.upsert(record)
    repository.clear()
    assert repository.list_sessions() == []


def test_history_handles_empty_and_corrupt_file(tmp_path: Path):
    repository = _repo(tmp_path)
    assert repository.list_sessions() == []
    repository.path.parent.mkdir(parents=True, exist_ok=True)
    repository.path.write_text("{corrupt", encoding="utf-8")
    assert repository.list_sessions() == []


def test_history_schema_version_compatibility(tmp_path: Path):
    repository = _repo(tmp_path)
    repository.path.parent.mkdir(parents=True, exist_ok=True)
    repository.path.write_text(
        json.dumps({"schema_version": SCHEMA_VERSION + 99, "sessions": [{"session_id": "old"}]}),
        encoding="utf-8",
    )
    from playlist_builder.ui.shared.history.errors import UnsupportedSchemaVersionError

    with pytest.raises(UnsupportedSchemaVersionError):
        repository.list_sessions()


def test_history_never_exposes_persistent_id():
    record = _sample_record()
    payload = record_to_dict(record)
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "persistent_id" not in encoded
    round_trip = record_from_dict(payload)
    assert round_trip.generation_request is not None
    assert "persistent_id" not in round_trip.generation_request


def test_bridge_list_history_and_get_history_session(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    backend = RuntimeEngineBridgeBackend(build_app_context())
    generated = backend.generate_playlist(
        PlaylistGenerationRequest(
            name="History Bridge",
            provider_id=ProviderId.APPLE_MUSIC,
            keywords=("history",),
            target_track_count=1,
        ),
        request_id="gen-bridge",
    )
    bridge = JsonRpcEngineBridge(backend=backend)
    listed = bridge.handle({"id": "hist-1", "command": BridgeCommand.LIST_HISTORY.value, "params": {}})
    assert listed[-1]["ok"] is True
    sessions = listed[-1]["result"]["sessions"]
    assert sessions
    session_id = sessions[0]["session_id"]
    details = bridge.handle(
        {
            "id": "hist-2",
            "command": BridgeCommand.GET_HISTORY_SESSION.value,
            "params": {"session_id": session_id},
        }
    )
    assert details[-1]["ok"] is True
    assert details[-1]["result"]["session"]["session_id"] == session_id
    assert generated.history_session_id == session_id


def test_bridge_delete_clear_export_and_replay(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    backend = RuntimeEngineBridgeBackend(build_app_context())
    generated = backend.generate_playlist(
        PlaylistGenerationRequest(
            name="Replay Demo",
            provider_id=ProviderId.APPLE_MUSIC,
            keywords=("replay",),
            target_track_count=1,
        ),
        request_id="gen-replay",
    )
    bridge = JsonRpcEngineBridge(backend=backend)
    session_id = generated.history_session_id
    replay = bridge.handle(
        {
            "id": "replay-1",
            "command": BridgeCommand.REPLAY_GENERATION.value,
            "params": {"session_id": session_id},
        }
    )
    assert replay[-1]["ok"] is True
    assert "generation" in replay[-1]["result"]

    export = bridge.handle(
        {
            "id": "exp-1",
            "command": BridgeCommand.EXPORT_HISTORY_SESSION.value,
            "params": {"session_id": session_id},
        }
    )
    assert export[-1]["ok"] is True
    assert export[-1]["result"]["export"]["session_id"] == session_id

    deleted = bridge.handle(
        {
            "id": "del-1",
            "command": BridgeCommand.DELETE_HISTORY_SESSION.value,
            "params": {"session_id": session_id},
        }
    )
    assert deleted[-1]["ok"] is True
    assert deleted[-1]["result"]["deleted"] is True

    cleared = bridge.handle({"id": "clr-1", "command": BridgeCommand.CLEAR_HISTORY.value, "params": {}})
    assert cleared[-1]["ok"] is True
    assert cleared[-1]["result"]["cleared"] is True

