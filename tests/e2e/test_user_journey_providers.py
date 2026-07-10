from __future__ import annotations

import json
from pathlib import Path

import pytest

from playlist_builder.ui.bridge import BridgeCommand
from tests.e2e.harness import E2EHarness, sample_remote_playlist_dict


@pytest.mark.integration
def test_integration_list_providers_apple_and_youtube_experimental(e2e_harness: E2EHarness) -> None:
    """Bridge list_providers — registry metadata only, no provider API calls."""
    result = e2e_harness.last_result(
        e2e_harness.call(BridgeCommand.LIST_PROVIDERS.value, request_id="list-providers")
    )
    providers = {item["provider_id"]: item for item in result["providers"]}
    assert "apple_music" in providers
    assert providers["apple_music"]["is_available"] is True
    assert "youtube_music" in providers
    assert providers["youtube_music"].get("is_experimental") is True


@pytest.mark.integration
def test_integration_load_remote_playlist_from_json_file(e2e_harness: E2EHarness, tmp_path: Path) -> None:
    """Bridge load_remote_playlist_from_file — parses local JSON, no import yet."""
    payload = {
        "provider_id": "youtube_music",
        "remote_playlist_id": "yt-file-1",
        "name": "YT File Import",
        "snapshot_at_iso": "2026-07-10T12:00:00",
        "track_count": 1,
        "checksum": "ytchecksum001",
        "source_kind": "file_import",
        "tracks": [
            {
                "remote_track_id": "yt-1",
                "artist": "Artist",
                "title": "Title",
                "position": 0,
            },
        ],
    }
    path = tmp_path / "remote_snapshot.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.LOAD_REMOTE_PLAYLIST_FROM_FILE.value,
            {"file_path": str(path)},
            request_id="load-file",
        )
    )
    snapshot = result["remote_playlist"]
    assert snapshot["provider_id"] == "youtube_music"
    assert snapshot["name"] == "YT File Import"


@pytest.mark.integration
def test_integration_diagnostics_observability_no_secret_leak(e2e_harness: E2EHarness) -> None:
    """Bridge diagnostics after sync plan — observability + plugins, no credential payload."""
    imported = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.IMPORT_REMOTE_PLAYLIST.value,
            {"remote_playlist": sample_remote_playlist_dict(checksum="diag-checksum")},
            request_id="import-diag",
        )
    )
    local_id = imported["playlist"]["local_playlist_id"]
    remote = sample_remote_playlist_dict(checksum="diag-checksum")
    remote["tracks"] = []

    e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.PLAN_SYNC.value,
            {
                "local_playlist_id": local_id,
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "dry_run",
                "remote_playlist": remote,
            },
            request_id="plan-for-diag",
        )
    )
    result = e2e_harness.last_result(
        e2e_harness.call(BridgeCommand.DIAGNOSTICS.value, request_id="diagnostics")
    )
    summary = result["summary"]
    assert "observability" in summary
    assert summary["observability"]["event_count"] >= 1
    assert "extension_points" in summary
    assert "extension_api_version" in summary
    assert result["engine_version"]

    blob = json.dumps(result).lower()
    for forbidden in ("cookie", "password", "secret", "bearer", "authorization"):
        assert forbidden not in blob
