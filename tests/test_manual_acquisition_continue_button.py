from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.app.bridge_runtime.backend import RuntimeEngineBridgeBackend
from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
from playlist_builder.app.bridge_runtime.import_stream import stream_import_playlist
from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings
from playlist_builder.canonical.compat import canonical_playlist_from_legacy
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackRef
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.ui.bridge.commands import ImportPlaylistResult
from playlist_builder.ui.shared.dto.enums import ImportPhase
from tests.manual_acquisition_test_support import (
    assert_identity_cache_miss,
    build_isolated_manual_context,
    install_explicit_manual_interruption_hook,
    stub_manual_acquisition_prerequisites,
)


def _playlist() -> PlaylistDefinition:
    return PlaylistDefinition(
        name="Test",
        sections=(
            PlaylistSection(
                name="Main",
                tracks=(TrackRef("A$AP Ferg", "Green Juice (feat. Pharrell Williams)"),),
            ),
        ),
    )


def _configure_catalog(context) -> MagicMock:
    resolver = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver
    applescript = resolver._applescript
    applescript.ensure_running = MagicMock()
    catalog_track = CanonicalTrack(
        artist=CanonicalArtist(name="A$AP Ferg"),
        title="Green Juice (feat. Pharrell Williams)",
    )
    catalog = MagicMock()
    catalog.search.return_value = CanonicalSearchResponse(
        request=CanonicalSearchRequest(query="A$AP Ferg Green Juice"),
        candidates=(
            CanonicalCandidate(
                track=catalog_track,
                source="itunes_catalog",
                provider_hints=("https://music.apple.com/us/song/green-juice/1",),
                raw_confidence=100.0,
            ),
        ),
    )
    resolver._catalog = catalog
    resolver._acquire_missing = True
    return applescript


def _session_id(events: list[object]) -> str:
    for event in events:
        payload = getattr(event, "payload", None)
        if isinstance(payload, dict) and payload.get("import_session_id"):
            return str(payload["import_session_id"])
    raise AssertionError("import_session_id missing from stream events")


def _canonical_pause_track() -> CanonicalTrack:
    return canonical_playlist_from_legacy(_playlist()).sections[0].tracks[0]


def _pause_for_manual_acquisition(monkeypatch, tmp_path) -> tuple[object, ImportSessionStore, str]:
    store = ImportSessionStore(tmp_path / "checkpoints")
    context = build_isolated_manual_context(tmp_path)
    applescript = _configure_catalog(context)
    stub_manual_acquisition_prerequisites(applescript)
    monkeypatch.setattr("playlist_builder.integration.apple_music.resolver.time.sleep", lambda _: None)
    install_explicit_manual_interruption_hook(monkeypatch)

    pause_track = _canonical_pause_track()
    assert_identity_cache_miss(context, pause_track)

    with patch.object(sys, "platform", "darwin"):
        pause_events = list(
            stream_import_playlist(
                context,
                _playlist(),
                "req-1",
                sync=True,
                write_json_diagnostics=False,
                session_store=store,
            )
        )
    pause_final = next(item for item in pause_events if isinstance(item, ImportPlaylistResult))
    assert pause_final.import_result.phase == ImportPhase.WAITING_FOR_MANUAL_ACQUISITION
    applescript.try_add_catalog_url.assert_called()
    applescript.open_catalog_url_for_manual.assert_called_once()
    return context, store, _session_id(pause_events)


def test_probe_manual_acquisition_caches_identity_when_found(monkeypatch, tmp_path):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch, tmp_path)
        resolver = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver
        applescript = resolver._applescript
        applescript.collect_candidates_batch = MagicMock(
            return_value=[
                [
                    AppleMusicTrack(
                        persistent_id="PID-MANUAL",
                        artist="A$AP Ferg",
                        title="Green Juice (feat. Pharrell Williams)",
                        query="Green Juice",
                    )
                ]
            ]
        )
        backend = RuntimeEngineBridgeBackend(context, session_store=store)
        result = backend.probe_manual_acquisition({"import_session_id": session_id})

    assert result["found"] is True
    cached = resolver._identity_cache.get(
        canonical_playlist_from_legacy(_playlist()).sections[0].tracks[0],
        ProviderId.APPLE_MUSIC,
    )
    assert cached is not None
    assert cached.external_id == "PID-MANUAL"


def test_probe_manual_acquisition_includes_timing_diagnostics(monkeypatch, tmp_path):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch, tmp_path)
        applescript = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver._applescript
        applescript.collect_candidates_batch = MagicMock(
            return_value=[
                [
                    AppleMusicTrack(
                        persistent_id="PID-MANUAL",
                        artist="A$AP Ferg",
                        title="Green Juice (feat. Pharrell Williams)",
                        query="Green Juice",
                    )
                ]
            ]
        )
        backend = RuntimeEngineBridgeBackend(context, session_store=store)
        result = backend.probe_manual_acquisition({"import_session_id": session_id})

    assert result["found"] is True
    assert isinstance(result["message"], str)
    assert result["message"]
    diagnostics = result["diagnostics"]
    assert diagnostics["import_session_id"] == session_id
    assert diagnostics["checkpoint_exists"] is True
    assert diagnostics["provider_id"] == ProviderId.APPLE_MUSIC.value
    assert diagnostics["search_terms"]
    assert diagnostics["checkpoint_path"].endswith(f"{session_id}.json")
    assert diagnostics["probe_duration_ms"] is not None
    assert diagnostics["probe_started_at"] is not None
    assert diagnostics["probe_finished_at"] is not None


def test_probe_manual_acquisition_track_not_found_message(monkeypatch, tmp_path):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch, tmp_path)
        applescript = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver._applescript
        applescript.collect_candidates_batch = MagicMock(return_value=[[]])
        backend = RuntimeEngineBridgeBackend(context, session_store=store)
        result = backend.probe_manual_acquisition({"import_session_id": session_id})

    assert result["found"] is False
    assert result["error_code"] == "track_not_found"
    assert "pas encore détecté" in result["message"].lower()


def test_probe_manual_acquisition_missing_checkpoint_structured(tmp_path):
    store = ImportSessionStore(tmp_path / "checkpoints")
    backend = RuntimeEngineBridgeBackend(
        build_app_context(AppSettings(wait_for_manual_catalog_add=True)),
        session_store=store,
    )
    with patch.object(sys, "platform", "darwin"):
        result = backend.probe_manual_acquisition({"import_session_id": "missing"})

    assert result["found"] is False
    assert result["error_code"] == "checkpoint_missing"
    assert "expiré" in result["message"].lower()
    assert result["diagnostics"]["checkpoint_exists"] is False


def test_probe_manual_acquisition_reports_probe_error(monkeypatch, tmp_path):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch, tmp_path)
        applescript = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver._applescript
        applescript.collect_candidates_batch = MagicMock(side_effect=RuntimeError("Music.app timeout"))
        backend = RuntimeEngineBridgeBackend(context, session_store=store)
        result = backend.probe_manual_acquisition({"import_session_id": session_id})

    assert result["found"] is False
    assert result["error_code"] == "probe_error"
    assert "Music.app timeout" in result["message"]
    assert result["diagnostics"]["probe_error"] == "Music.app timeout"


def test_continue_manual_acquisition_after_probe_found(monkeypatch, tmp_path):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch, tmp_path)
        applescript = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver._applescript
        applescript.collect_candidates_batch = MagicMock(
            return_value=[
                [
                    AppleMusicTrack(
                        persistent_id="PID-MANUAL",
                        artist="A$AP Ferg",
                        title="Green Juice (feat. Pharrell Williams)",
                        query="Green Juice",
                    )
                ]
            ]
        )
        backend = RuntimeEngineBridgeBackend(context, session_store=store)
        probe = backend.probe_manual_acquisition({"import_session_id": session_id})
        assert probe["found"] is True

        resume_events: list[object] = []
        try:
            for item in backend.continue_manual_acquisition_stream({"import_session_id": session_id}):
                resume_events.append(item)
        except FileNotFoundError:
            pass

        assert any(
            getattr(event, "payload", {}).get("phase") == ImportPhase.RESOLVING.value
            for event in resume_events
            if hasattr(event, "payload")
        )


def test_resume_skips_catalog_reopen_on_confirmed_manual(monkeypatch, tmp_path):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch, tmp_path)
        applescript = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver._applescript
        applescript.collect_candidates_batch = MagicMock(
            side_effect=[
                [[]],
                [
                    [
                        AppleMusicTrack(
                            persistent_id="PID-MANUAL",
                            artist="A$AP Ferg",
                            title="Green Juice (feat. Pharrell Williams)",
                            query="Green Juice",
                        )
                    ]
                ],
            ]
        )
        backend = RuntimeEngineBridgeBackend(context, session_store=store)
        applescript.open_catalog_url_for_manual.reset_mock()
        try:
            list(backend.continue_manual_acquisition_stream({"import_session_id": session_id}))
        except FileNotFoundError:
            pass

        applescript.open_catalog_url_for_manual.assert_not_called()
