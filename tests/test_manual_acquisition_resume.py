from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.app.bridge_runtime.backend import RuntimeEngineBridgeBackend
from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
from playlist_builder.app.bridge_runtime.import_stream import stream_import_playlist
from playlist_builder.canonical.compat import canonical_playlist_from_legacy
from playlist_builder.canonical.enums import ImportStatus, ProviderId
from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalImportReport,
    CanonicalImportResult,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackRef
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.integration.ports.provider_import import ProviderImportResolutionStatus
from playlist_builder.ui.bridge.commands import ImportPlaylistResult
from playlist_builder.ui.bridge.events import BridgeEventType
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
                tracks=(TrackRef("Dwayne Johnson", "You're Welcome"),),
            ),
        ),
    )


def _canonical_pause_track() -> CanonicalTrack:
    return canonical_playlist_from_legacy(_playlist()).sections[0].tracks[0]


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


def _manual_pause_events(events: list[object]) -> list[object]:
    return [
        event
        for event in events
        if getattr(event, "event", None) == BridgeEventType.MANUAL_ACQUISITION_REQUIRED
    ]


def test_manual_acquisition_resume_does_not_repause_when_library_visible(monkeypatch, tmp_path):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch, tmp_path)
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


def test_manual_acquisition_resume_probes_library_after_confirmation(monkeypatch, tmp_path):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch, tmp_path)
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


def test_probe_manual_acquisition_uses_checkpoint_track(monkeypatch, tmp_path):
    with patch.object(sys, "platform", "darwin"):
        context, store, session_id = _pause_for_manual_acquisition(monkeypatch, tmp_path)
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


@patch.object(sys, "platform", "darwin")
def test_identity_cache_hit_completes_without_manual_pause(monkeypatch, tmp_path):
    """A warm IdentityCache legitimately bypasses manual acquisition and completes import."""
    store = ImportSessionStore(tmp_path / "checkpoints")
    context = build_isolated_manual_context(tmp_path)
    resolver = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver
    pause_track = _canonical_pause_track()
    resolver._identity_cache.put_identity(
        pause_track,
        provider_id=ProviderId.APPLE_MUSIC,
        external_id="PID-CACHED",
        confidence=100.0,
    )

    applescript = _configure_catalog(context)
    stub_manual_acquisition_prerequisites(applescript)
    monkeypatch.setattr("playlist_builder.integration.apple_music.resolver.time.sleep", lambda _: None)

    import_port = __import__(
        "playlist_builder.app.factory",
        fromlist=["get_provider_import_port"],
    ).get_provider_import_port(context)

    def fake_deliver(playlist_arg, outcomes, **kwargs):
        return CanonicalImportReport(
            playlist_name=playlist_arg.name,
            results=tuple(
                CanonicalImportResult(
                    track=outcome.track,
                    status=ImportStatus.ADDED,
                    section_name="Main",
                )
                for outcome in outcomes
                if outcome.status == ProviderImportResolutionStatus.RESOLVED
            ),
        )

    import_port.deliver_playlist = fake_deliver
    import_port.ensure_playlist = MagicMock()
    monkeypatch.setattr(
        "playlist_builder.app.bridge_runtime.import_stream.get_provider_import_port",
        lambda *_args, **_kwargs: import_port,
    )

    events = list(
        stream_import_playlist(
            context,
            _playlist(),
            "req-cache-hit",
            sync=True,
            write_json_diagnostics=False,
            session_store=store,
        )
    )
    final = next(item for item in events if isinstance(item, ImportPlaylistResult))
    assert final.import_result.phase == ImportPhase.COMPLETED
    applescript.open_catalog_url_for_manual.assert_not_called()
    applescript.try_add_catalog_url.assert_not_called()
