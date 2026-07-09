from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.app.bridge_runtime.retry_import import stream_retry_import_tracks
from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackAddResult, TrackAddStatus, TrackRef
from playlist_builder.ui.bridge.commands import ImportPlaylistResult
from playlist_builder.ui.bridge.json_rpc import JsonRpcEngineBridge
from playlist_builder.ui.shared.dto.enums import ImportPhase, ImportTrackStatus


def _five_track_playlist() -> PlaylistDefinition:
    return PlaylistDefinition(
        name="Retry Baseline",
        sections=(
            PlaylistSection(
                name="Main",
                tracks=(
                    TrackRef("Artist A", "Track A"),
                    TrackRef("Artist B", "Track B"),
                    TrackRef("Artist C", "Track C"),
                    TrackRef("Artist D", "Track D"),
                    TrackRef("Artist E", "Track E"),
                ),
            ),
        ),
    )


def _existing_results() -> list[TrackAddResult]:
    return [
        TrackAddResult(track=TrackRef("Artist A", "Track A"), status=TrackAddStatus.ADDED, error="Ajouté"),
        TrackAddResult(track=TrackRef("Artist B", "Track B"), status=TrackAddStatus.SKIPPED, error="Déjà présent"),
        TrackAddResult(track=TrackRef("Artist C", "Track C"), status=TrackAddStatus.NOT_FOUND, error="Introuvable"),
        TrackAddResult(track=TrackRef("Artist D", "Track D"), status=TrackAddStatus.ERROR, error="Erreur"),
        TrackAddResult(track=TrackRef("Artist E", "Track E"), status=TrackAddStatus.NOT_FOUND, error="Non importé"),
    ]


@patch.object(sys, "platform", "darwin")
def test_retry_import_preserves_existing_results_for_untouched_tracks(monkeypatch):
    from playlist_builder.canonical.enums import ImportStatus
    from playlist_builder.canonical.models import CanonicalArtist, CanonicalTrack
    from playlist_builder.integration.ports.provider_import import (
        ProviderImportResolutionOutcome,
        ProviderImportResolutionStatus,
    )

    playlist = _five_track_playlist()
    context = build_app_context(AppSettings())
    import_port = MagicMock()
    import_port.runtime_labels = MagicMock(not_found_message="Introuvable")
    resolved_track = CanonicalTrack(artist=CanonicalArtist(name="Artist E"), title="Track E")
    import_port.resolve.return_value = ProviderImportResolutionOutcome(
        track=resolved_track,
        status=ProviderImportResolutionStatus.RESOLVED,
    )
    import_port.add_resolved_track.return_value = MagicMock(status=ImportStatus.ADDED, error="")

    monkeypatch.setattr(
        "playlist_builder.app.bridge_runtime.retry_import.get_provider_import_port",
        lambda *_args, **_kwargs: import_port,
    )

    events = list(
        stream_retry_import_tracks(
            context,
            playlist,
            "retry-req",
            track_indices=[4],
            existing_results=_existing_results(),
        )
    )
    final = next(item for item in events if isinstance(item, ImportPlaylistResult))

    assert len(final.import_result.outcomes) == 5
    assert final.import_result.outcomes[0].status == ImportTrackStatus.ADDED
    assert final.import_result.outcomes[1].status == ImportTrackStatus.SKIPPED
    assert final.import_result.outcomes[2].status == ImportTrackStatus.NOT_FOUND
    assert final.import_result.outcomes[3].status == ImportTrackStatus.ERROR
    assert final.import_result.outcomes[4].status == ImportTrackStatus.ADDED


def test_json_rpc_retry_passes_existing_outcomes_to_backend():
    backend = MagicMock()
    backend.retry_import_tracks_stream.return_value = [
        ImportPlaylistResult(
            import_result=__import__(
                "playlist_builder.ui.shared.dto.import_state",
                fromlist=["ImportResultState"],
            ).ImportResultState(playlist_name="Retry Baseline", phase=ImportPhase.COMPLETED)
        )
    ]
    bridge = JsonRpcEngineBridge(backend=backend)
    request = {
        "id": "retry-json",
        "command": "retry_import_tracks",
        "params": {
            "playlist": {
                "name": "Retry Baseline",
                "sections": [
                    {
                        "name": "Main",
                        "tracks": [
                            {"artist": "Artist A", "title": "Track A"},
                            {"artist": "Artist B", "title": "Track B"},
                        ],
                    }
                ],
            },
            "track_indices": [1],
            "existing_outcomes": [
                {
                    "artist": "Artist A",
                    "title": "Track A",
                    "section": "Main",
                    "status": "added",
                    "message": "Ajouté",
                },
                {
                    "artist": "Artist B",
                    "title": "Track B",
                    "section": "Main",
                    "status": "not_found",
                    "message": "Introuvable",
                },
            ],
        },
    }

    responses = bridge.handle(request)
    assert any(item.get("event") == "completed" for item in responses if isinstance(item, dict))
    kwargs = backend.retry_import_tracks_stream.call_args.kwargs
    existing = kwargs["existing_results"]
    assert existing is not None
    assert len(existing) == 2
    assert existing[0].status == TrackAddStatus.ADDED
    assert existing[1].status == TrackAddStatus.NOT_FOUND
