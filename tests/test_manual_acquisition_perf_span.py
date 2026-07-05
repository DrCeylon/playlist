from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

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
from playlist_builder.ui.bridge.commands import ImportPlaylistResult
from playlist_builder.ui.shared.dto.enums import ImportPhase


def test_manual_acquisition_survives_perf_span_context_manager():
    """Regression: frozen dataclass exceptions broke perf_span __exit__ traceback attach."""
    with patch.object(sys, "platform", "darwin"):
        context = build_app_context(AppSettings(wait_for_manual_catalog_add=True))
        resolver = context.registry.get(ProviderId.APPLE_MUSIC).import_service.resolver
        applescript = resolver._applescript
        applescript.ensure_running = MagicMock()
        applescript.collect_candidates_batch = MagicMock(return_value=[[]])
        applescript.try_add_catalog_url = MagicMock(return_value="")
        applescript.open_catalog_url_for_manual = MagicMock()

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

        playlist = PlaylistDefinition(
            name="Test",
            sections=(
                PlaylistSection(
                    name="Main",
                    tracks=(TrackRef("Dwayne Johnson", "You're Welcome"),),
                ),
            ),
        )

        events = list(
            stream_import_playlist(
                context,
                playlist,
                "req-1",
                sync=True,
                write_json_diagnostics=False,
                session_store=ImportSessionStore(),
            )
        )

    final = next(item for item in events if isinstance(item, ImportPlaylistResult))
    assert final.import_result.phase == ImportPhase.WAITING_FOR_MANUAL_ACQUISITION
    applescript.try_add_catalog_url.assert_called()
    applescript.open_catalog_url_for_manual.assert_called_once()
