from __future__ import annotations

import pytest

from playlist_builder.observability import get_default_bus
from playlist_builder.observability.events import EventCategory
from playlist_builder.ui.bridge import BridgeCommand
from tests.e2e.harness import E2EHarness, sample_remote_playlist_dict


@pytest.mark.e2e
def test_e2e_import_remote_repository_plan_sync(e2e_harness: E2EHarness) -> None:
    """True E2E: bridge import_remote → persisted repository/snapshot → plan_sync dry_run."""
    imported = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.IMPORT_REMOTE_PLAYLIST.value,
            {"remote_playlist": sample_remote_playlist_dict(checksum="chain-import-01")},
            request_id="import-chain",
        )
    )
    local_id = imported["playlist"]["local_playlist_id"]
    assert e2e_harness.settings.managed_playlists_path.exists()
    assert list(e2e_harness.settings.playlist_snapshots_dir.glob("*.json"))

    remote = sample_remote_playlist_dict(checksum="chain-import-01")
    remote["tracks"] = []
    plan = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.PLAN_SYNC.value,
            {
                "local_playlist_id": local_id,
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "dry_run",
                "remote_playlist": remote,
            },
            request_id="plan-chain",
        )
    )
    assert plan["sync_plan"]["sync_mode"] == "dry_run"
    assert not e2e_harness.settings.sync_operations_path.exists()


@pytest.mark.e2e
def test_e2e_sync_dry_run_then_apply_append(e2e_harness: E2EHarness) -> None:
    """True E2E: import → plan dry_run → plan append → apply_sync → persistence + observability."""
    import_result = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.IMPORT_REMOTE_PLAYLIST.value,
            {"remote_playlist": sample_remote_playlist_dict(checksum="checksum-sync-01")},
            request_id="import-for-sync",
        )
    )
    local_id = import_result["playlist"]["local_playlist_id"]
    remote = sample_remote_playlist_dict(checksum="checksum-sync-01")
    remote["tracks"] = []

    plan = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.PLAN_SYNC.value,
            {
                "local_playlist_id": local_id,
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "dry_run",
                "remote_playlist": remote,
            },
            request_id="plan-dry",
        )
    )
    assert plan["sync_plan"]["sync_mode"] == "dry_run"

    bus = get_default_bus()
    before_apply = bus.event_count()

    remote_apply = sample_remote_playlist_dict(checksum="checksum-sync-01")
    remote_apply["tracks"] = []
    plan_apply = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.PLAN_SYNC.value,
            {
                "local_playlist_id": local_id,
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "append_only",
                "remote_playlist": remote_apply,
            },
            request_id="plan-apply",
        )
    )
    apply_result = e2e_harness.sync_apply(
        e2e_harness.call(
            BridgeCommand.APPLY_SYNC.value,
            {
                "local_playlist_id": local_id,
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "append_only",
                "remote_playlist": remote_apply,
                "plan_checksum": plan_apply["plan_checksum"],
                "expected_local_playlist_version": import_result["playlist"]["playlist_version"],
                "expected_remote_snapshot_checksum": remote_apply["checksum"],
                "confirm_destructive": False,
            },
            request_id="apply-sync",
        )
    )
    assert apply_result["final_sync_status"] == "synced"
    assert e2e_harness.write_port.upserted
    assert e2e_harness.settings.sync_operations_path.exists()

    sync_events = bus.recent_events(category=EventCategory.SYNC)
    assert any(event.kind.value == "sync.apply.completed" for event in sync_events)
    assert bus.event_count() > before_apply
