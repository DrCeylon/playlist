from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.app.bridge_runtime.backend import RuntimeEngineBridgeBackend
from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
from playlist_builder.app.bridge_runtime.import_stream import stream_import_playlist
from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings
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
from playlist_builder.ui.bridge.events import BridgeEventType
from playlist_builder.ui.shared.dto.enums import ImportPhase


def _playlist() -> PlaylistDefinition:
    return PlaylistDefinition(
        name="Test",
        sections=(
            PlaylistSection(
                name="Main",
                tracks=(TrackRef("Dwayne Johnson", "You're Welcome"),),
            ),
        ),
    )


def _configure_catalog(context) -> MagicMock:
    resolver = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver
    applescript = resolver._applescript
    applescript.ensure_running = MagicMock()
    catalog_track = CanonicalTrack(
        artist=CanonicalArtist(name="Dwayne Johnson"),
        title="You're Welcome",
    )
    catalog = MagicMock()
    catalog.search.return_value = CanonicalSearchResponse(
        request=CanonicalSearchRequest(query="Dwayne Johnson You're Welcome"),
        candidates=(
            CanonicalCandidate(
                track=catalog_track,
                source="itunes_catalog",
                provider_hints=(
                    "https://music.apple.com/us/song/youre-welcome/6779424544",
                    "itunes_track_id:6779424544",
                ),
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


def _pause_for_manual_acquisition(monkeypatch) -> tuple[object, ImportSessionStore, str]:
    store = ImportSessionStore()
    context = build_app_context(AppSettings(wait_for_manual_catalog_add=True))
    applescript = _configure_catalog(context)
    applescript.collect_candidates_batch = MagicMock(return_value=[[]])
    applescript.try_add_catalog_url = MagicMock(return_value="")
    applescript.open_catalog_url_for_manual = MagicMock()
    monkeypatch.setattr("playlist_builder.integration.apple_music.resolver.time.sleep", lambda _: None)

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
    return context, store, _session_id(pause_events)


def _manual_pause_events(events: list[object]) -> list[object]:
    return [
        event
        for event in events
        if getattr(event, "event", None) == BridgeEventType.MANUAL_ACQUISITION_REQUIRED
    ]


def test_manual_acquisition_resume_does_not_repause_when_library_visible(monkeypatch):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch)
        applescript = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver._applescript
        applescript.collect_candidates_batch = MagicMock(
            return_value=[
                [
                    AppleMusicTrack(
                        persistent_id="PID-MANUAL",
                        artist="Dwayne Johnson",
                        title="You're Welcome",
                        query="You're Welcome",
                    )
                ]
            ]
        )

        backend = RuntimeEngineBridgeBackend(context, session_store=store)
        resume_events: list[object] = []
        try:
            for item in backend.continue_manual_acquisition_stream({"import_session_id": session_id}):
                resume_events.append(item)
        except FileNotFoundError:
            # Delivery may reach real AppleScript on Linux; resolution already resumed.
            pass

        assert _manual_pause_events(resume_events) == []
        assert any(
            getattr(event, "payload", {}).get("phase") == ImportPhase.RESOLVING.value
            for event in resume_events
            if hasattr(event, "payload")
        )


def test_manual_acquisition_resume_probes_library_after_confirmation(monkeypatch):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch)
        applescript = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver._applescript
        applescript.collect_candidates_batch = MagicMock(
            side_effect=[
                [[]],
                [[]],
                [[]],
                [[]],
                [
                    [
                        AppleMusicTrack(
                            persistent_id="PID-MANUAL",
                            artist="Dwayne Johnson",
                            title="You're Welcome",
                            query="You're Welcome",
                        )
                    ]
                ],
            ]
        )
        applescript.try_add_catalog_url = MagicMock(return_value="")

        backend = RuntimeEngineBridgeBackend(context, session_store=store)
        resume_events: list[object] = []
        try:
            for item in backend.continue_manual_acquisition_stream({"import_session_id": session_id}):
                resume_events.append(item)
        except FileNotFoundError:
            pass

        assert _manual_pause_events(resume_events) == []
        assert applescript.collect_candidates_batch.call_count >= 5


def test_probe_manual_acquisition_uses_checkpoint_track(monkeypatch):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch)
        applescript = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver._applescript
        applescript.collect_candidates_batch = MagicMock(
            return_value=[
                [
                    AppleMusicTrack(
                        persistent_id="PID-MANUAL",
                        artist="Dwayne Johnson",
                        title="You're Welcome",
                        query="You're Welcome",
                    )
                ]
            ]
        )

        backend = RuntimeEngineBridgeBackend(context, session_store=store)
        result = backend.probe_manual_acquisition({"import_session_id": session_id})

    assert result["found"] is True
