from __future__ import annotations

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.app.bridge_runtime.import_session import ImportSessionCheckpoint, ImportSessionStore
from playlist_builder.app.bridge_runtime.import_stream import (
    _prefill_resolved_outcomes_before_checkpoint,
    stream_import_playlist,
)
from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings
from playlist_builder.canonical.enums import ImportStatus, ProviderId
from playlist_builder.canonical.models import CanonicalArtist, CanonicalImportReport, CanonicalImportResult, CanonicalTrack
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackRef
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.integration.ports.provider_import import ProviderImportResolutionOutcome, ProviderImportResolutionStatus
from playlist_builder.ui.bridge.commands import ImportPlaylistResult
from playlist_builder.ui.shared.dto.enums import ImportPhase, ImportTrackStatus


def _three_track_playlist() -> PlaylistDefinition:
    return PlaylistDefinition(
        name="Resume Align",
        sections=(
            PlaylistSection(
                name="Main",
                tracks=(
                    TrackRef("Artist A", "Track A"),
                    TrackRef("Artist B", "Track B"),
                    TrackRef("Artist C", "Track C"),
                ),
            ),
        ),
    )


def _canonical_track(artist: str, title: str) -> CanonicalTrack:
    return CanonicalTrack(artist=CanonicalArtist(name=artist), title=title)


def test_prefill_resolved_outcomes_before_checkpoint_rebuilds_prefix_rows():
    rows = [
        (_canonical_track("Artist A", "Track A"), "Main"),
        (_canonical_track("Artist B", "Track B"), "Main"),
        (_canonical_track("Artist C", "Track C"), "Main"),
    ]
    import_port = MagicMock()
    import_port.resolve_batch.return_value = [
        ProviderImportResolutionOutcome(
            track=rows[0][0],
            status=ProviderImportResolutionStatus.RESOLVED,
            cache_hit=True,
        ),
        ProviderImportResolutionOutcome(
            track=rows[1][0],
            status=ProviderImportResolutionStatus.RESOLVED,
            cache_hit=True,
        ),
    ]

    prefilled = _prefill_resolved_outcomes_before_checkpoint(import_port, rows, start_index=2)

    assert len(prefilled) == 2
    import_port.resolve_batch.assert_called_once()
    batch_arg = import_port.resolve_batch.call_args.args[0]
    assert len(batch_arg) == 2
    assert batch_arg[0][1] == "Main"
    assert batch_arg[1][0].title == "Track B"


def test_prefill_resolved_outcomes_before_checkpoint_noop_at_zero():
    import_port = MagicMock()
    assert _prefill_resolved_outcomes_before_checkpoint(import_port, [], start_index=0) == []
    import_port.resolve_batch.assert_not_called()


@patch.object(sys, "platform", "darwin")
def test_resume_with_checkpoint_next_index_delivers_full_outcome_list(monkeypatch, tmp_path, caplog):
    playlist = _three_track_playlist()
    store = ImportSessionStore(tmp_path / "checkpoints")
    session_id = "resume-align-session"
    store.save(
        ImportSessionCheckpoint(
            session_id=session_id,
            playlist=playlist,
            next_index=2,
            request_id="req-resume-align",
            sync=True,
            write_json_diagnostics=False,
            history_session_id="",
        )
    )

    context = build_app_context(AppSettings(wait_for_manual_catalog_add=True))
    resolver = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver
    identity_cache = resolver._identity_cache
    identity_cache.put_identity(
        _canonical_track("Artist A", "Track A"),
        provider_id=ProviderId.APPLE_MUSIC,
        external_id="PID-A",
        confidence=100.0,
    )
    identity_cache.put_identity(
        _canonical_track("Artist B", "Track B"),
        provider_id=ProviderId.APPLE_MUSIC,
        external_id="PID-B",
        confidence=100.0,
    )

    applescript = resolver._applescript
    applescript.ensure_running = MagicMock()
    applescript.ensure_playlist = MagicMock()
    applescript.collect_candidates_batch = MagicMock(
        return_value=[
            [
                AppleMusicTrack(
                    persistent_id="PID-C",
                    artist="Artist C",
                    title="Track C",
                    query="Track C",
                )
            ]
        ]
    )
    monkeypatch.setattr("playlist_builder.integration.apple_music.resolver.time.sleep", lambda _: None)

    delivered_outcome_counts: list[int] = []
    import_port = __import__(
        "playlist_builder.app.factory",
        fromlist=["get_provider_import_port"],
    ).get_provider_import_port(context)

    def fake_deliver(playlist_arg, outcomes, **kwargs):
        delivered_outcome_counts.append(len(outcomes))
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

    import_port.ensure_playlist = MagicMock()
    import_port.deliver_playlist = fake_deliver
    monkeypatch.setattr(
        "playlist_builder.app.bridge_runtime.import_stream.get_provider_import_port",
        lambda *_args, **_kwargs: import_port,
    )

    caplog.set_level(logging.ERROR)
    checkpoint = store.load(session_id)
    assert checkpoint is not None

    events: list[object] = []
    for item in stream_import_playlist(
        context,
        playlist,
        "req-resume-align",
        sync=True,
        write_json_diagnostics=False,
        session_store=store,
        checkpoint=checkpoint,
    ):
        events.append(item)

    final = next(item for item in events if isinstance(item, ImportPlaylistResult))
    assert delivered_outcome_counts == [3]
    assert "Resolution outcomes count mismatch" not in caplog.text
    assert final.import_result.phase == ImportPhase.COMPLETED
    assert final.import_result.added_count == 3
    assert all(outcome.status == ImportTrackStatus.ADDED for outcome in final.import_result.outcomes)
