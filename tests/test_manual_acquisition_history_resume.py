from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.app.bridge_runtime.backend import RuntimeEngineBridgeBackend
from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings
from playlist_builder.ui.shared.dto import ImportPhase, ImportResultState, ImportTrackOutcome, ImportTrackStatus
from playlist_builder.ui.shared.history import HistorySessionStatus, SessionHistoryRepository, SessionHistoryService


def test_import_result_state_carries_manual_resume_metadata():
    state = ImportResultState(
        playlist_name="Demo",
        outcomes=(ImportTrackOutcome("A", "B", "Main", ImportTrackStatus.ACQUIRING, "wait"),),
        phase=ImportPhase.WAITING_FOR_MANUAL_ACQUISITION,
        import_session_id="bridge-session-1",
        manual_token="track-key",
        manual_artist="A",
        manual_title="B",
        manual_instructions="Ajoutez dans Music.app",
        manual_catalog_url="https://music.apple.com/song/1",
    )

    assert state.import_session_id == "bridge-session-1"
    assert state.manual_artist == "A"
    assert state.manual_title == "B"


def test_history_persists_manual_resume_metadata(tmp_path):
    service = SessionHistoryService(SessionHistoryRepository(tmp_path / "sessions.json"))
    created = service.create_generation_session(
        request_id="gen-1",
        playlist_name="Demo",
        provider_id=ProviderId.APPLE_MUSIC,
        generation_request={"name": "Demo"},
        generation_result={"playlist_name": "Demo"},
        track_count=1,
    )
    updated = service.attach_import_result(
        session_id=created.session_id,
        playlist_name="Demo",
        provider_id=created.provider_id,
        result=ImportResultState(
            playlist_name="Demo",
            phase=ImportPhase.WAITING_FOR_MANUAL_ACQUISITION,
            outcomes=(ImportTrackOutcome("A", "B", "Main", ImportTrackStatus.ACQUIRING, "wait"),),
            import_session_id="bridge-session-1",
            manual_artist="A",
            manual_title="B",
            manual_instructions="instructions",
        ),
    )

    assert updated.status == HistorySessionStatus.WAITING_FOR_MANUAL_ACQUISITION
    assert updated.import_result is not None
    assert updated.import_result["import_session_id"] == "bridge-session-1"
    assert updated.import_result["manual_artist"] == "A"


def test_probe_manual_acquisition_reports_missing_checkpoint(tmp_path):
    backend = RuntimeEngineBridgeBackend(
        build_app_context(AppSettings(wait_for_manual_catalog_add=True)),
        session_store=ImportSessionStore(tmp_path / "checkpoints"),
    )
    with patch.object(sys, "platform", "darwin"):
        result = backend.probe_manual_acquisition({"import_session_id": "missing"})

    assert result["found"] is False
    assert "introuvable" in result["message"].lower() or "expiré" in result["message"].lower()
    assert result.get("error_code") == "checkpoint_missing"
    assert result["diagnostics"]["checkpoint_exists"] is False


def test_import_session_store_uses_persistent_data_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = ImportSessionStore()
    assert store._root == __import__("pathlib").Path("data/imports/checkpoints")
