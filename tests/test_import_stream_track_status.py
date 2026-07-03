"""Regression tests for import stream track progress (ImportTrackStatus shadowing)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
from playlist_builder.app.bridge_runtime.import_stream import stream_import_playlist
from playlist_builder.canonical.enums import ImportStatus, ProviderId
from playlist_builder.canonical.models import CanonicalArtist, CanonicalImportReport, CanonicalImportResult, CanonicalTrack
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackRef
from playlist_builder.integration.apple_music.resolver import (
    AppleMusicResolutionOutcome,
    AppleMusicResolutionStatus,
)


def _mock_context() -> MagicMock:
    track = CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone")
    outcome = AppleMusicResolutionOutcome(
        track=track,
        persistent_id="PID-1",
        status=AppleMusicResolutionStatus.RESOLVED,
    )
    resolver = MagicMock()
    resolver.resolve.return_value = outcome
    resolver._applescript = MagicMock()

    report = CanonicalImportReport(
        playlist_name="Pool Party",
        results=(
            CanonicalImportResult(
                track=track,
                status=ImportStatus.ADDED,
                section_name="Main",
            ),
        ),
    )
    delivery = MagicMock()
    delivery.sync_playlist.return_value = report

    import_service = MagicMock()
    import_service.resolver = resolver
    import_service.delivery = delivery

    gateway = MagicMock()
    gateway.import_service = import_service

    registry = MagicMock()
    registry.get.return_value = gateway

    context = MagicMock()
    context.registry = registry
    context.settings.wait_for_manual_catalog_add = False
    return context


def test_stream_import_playlist_emits_track_progress_without_import_track_status_shadowing():
    """ImportTrackStatus must stay module-level — a local import broke resolution (Phase 5.1.2 P0)."""
    playlist = PlaylistDefinition(
        name="Pool Party",
        sections=(
            PlaylistSection(
                name="Main",
                tracks=(TrackRef("Kygo", "Firestone", section="Main"),),
            ),
        ),
    )
    context = _mock_context()

    with patch.object(sys, "platform", "darwin"):
        events = list(
            stream_import_playlist(
                context,
                playlist,
                "req-track-status",
                sync=True,
                write_json_diagnostics=False,
                session_store=ImportSessionStore(),
            )
        )

    track_progress = [
        event
        for event in events
        if getattr(event, "event", None) == "track_progress"
    ]
    assert track_progress, "expected track_progress events during resolution"
    first_payload = track_progress[0].payload
    assert first_payload["status"] in {"pending", "added", "not_found", "error", "skipped"}


def test_import_stream_module_does_not_reimport_import_track_status_inside_function():
    import ast
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / "playlist_builder" / "app" / "bridge_runtime" / "import_stream.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "stream_import_playlist":
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.ImportFrom) and child.module == "playlist_builder.ui.shared.dto.enums":
                imported = [alias.name for alias in child.names]
                if "ImportTrackStatus" in imported:
                    offenders.append(f"line {child.lineno}")
    assert offenders == []
