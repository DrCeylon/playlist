from __future__ import annotations

import pytest

from playlist_builder.ui.bridge import BridgeCommand
from tests.e2e.harness import E2EHarness


class _HistoryBackendMixin:
    """Inject minimal history into RuntimeEngineBridgeBackend for migration E2E."""

    def list_history(self) -> tuple[dict[str, object], ...]:
        return (
            {
                "session_id": "sess-e2e-1",
                "playlist_name": "Migrated Playlist",
                "provider_id": "apple_music",
                "status": "imported",
                "track_count": 1,
                "finished_at_iso": "2026-07-10T10:00:00",
                "started_at_iso": "2026-07-10T09:00:00",
                "import_result": {
                    "outcomes": [
                        {"artist": "Daft Punk", "title": "One More Time", "section": "Main", "status": "added"},
                    ],
                },
            },
        )


@pytest.mark.integration
def test_integration_history_migration_via_list_managed_playlists(e2e_harness: E2EHarness) -> None:
    """Scenario: history.migration + migration.history_idempotent"""
    e2e_harness.backend.list_history = _HistoryBackendMixin.list_history.__get__(  # type: ignore[method-assign]
        e2e_harness.backend,
        type(e2e_harness.backend),
    )
    first = e2e_harness.last_result(
        e2e_harness.call(BridgeCommand.LIST_MANAGED_PLAYLISTS.value, request_id="list-1")
    )
    second = e2e_harness.last_result(
        e2e_harness.call(BridgeCommand.LIST_MANAGED_PLAYLISTS.value, request_id="list-2")
    )
    assert len(first["playlists"]) == 1
    assert len(second["playlists"]) == 1
    assert first["playlists"][0]["local_playlist_id"] == second["playlists"][0]["local_playlist_id"]
    assert first["playlists"][0]["local_playlist_id"].startswith("hist-")
