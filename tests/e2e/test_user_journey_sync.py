from __future__ import annotations

import pytest

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.observability import get_default_bus
from playlist_builder.observability.events import EventCategory
from playlist_builder.ui.bridge import BridgeCommand
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
from tests.e2e.harness import E2EHarness, FakeWritePort, build_e2e_harness, sample_remote_playlist_dict


@pytest.mark.e2e
def test_e2e_import_remote_creates_repository_and_snapshot(e2e_harness: E2EHarness) -> None:
    """Scenario: import.file.remote + create.local.repository + snapshot.archive"""
    result = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.IMPORT_REMOTE_PLAYLIST.value,
            {"remote_playlist": sample_remote_playlist_dict()},
            request_id="import-remote",
        )
    )
    playlist = result["playlist"]
    local_id = playlist["local_playlist_id"]
    assert playlist["origin"] == "provider_library"
    assert playlist["linked_remote_refs"][0]["snapshot_checksum"] == "deadbeefcafebabe"

    assert e2e_harness.settings.managed_playlists_path.exists()
    snapshots = list(e2e_harness.settings.playlist_snapshots_dir.glob("*.json"))
    assert len(snapshots) == 1

    listed = e2e_harness.last_result(
        e2e_harness.call(BridgeCommand.LIST_MANAGED_PLAYLISTS.value, request_id="list-pl")
    )
    assert any(item["local_playlist_id"] == local_id for item in listed["playlists"])


@pytest.mark.e2e
def test_e2e_sync_dry_run_then_apply_append(e2e_harness: E2EHarness) -> None:
    """Scenario: sync.dry_run + sync.apply.append"""
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
    apply_result = e2e_harness.last_result(
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
    assert apply_result["sync_apply"]["final_sync_status"] == "synced"
    assert e2e_harness.write_port.upserted
    assert e2e_harness.settings.sync_operations_path.exists()

    sync_events = bus.recent_events(category=EventCategory.SYNC)
    assert any(event.kind.value == "sync.apply.completed" for event in sync_events)
    assert bus.event_count() > before_apply


@pytest.mark.integration
def test_integration_partial_sync_write_failure(tmp_path) -> None:
    """Scenario: sync.partial_failure"""
    harness = build_e2e_harness(tmp_path, write_port=FakeWritePort(fail_on_call=1))
    import_result = harness.last_result(
        harness.call(
            BridgeCommand.IMPORT_REMOTE_PLAYLIST.value,
            {"remote_playlist": sample_remote_playlist_dict(checksum="partial-01")},
        )
    )
    local_id = import_result["playlist"]["local_playlist_id"]
    remote = sample_remote_playlist_dict(checksum="partial-01")
    remote["tracks"] = []
    plan = harness.last_result(
        harness.call(
            BridgeCommand.PLAN_SYNC.value,
            {
                "local_playlist_id": local_id,
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "append_only",
                "remote_playlist": remote,
            },
        )
    )
    apply_result = harness.last_result(
        harness.call(
            BridgeCommand.APPLY_SYNC.value,
            {
                "local_playlist_id": local_id,
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "append_only",
                "remote_playlist": remote,
                "plan_checksum": plan["plan_checksum"],
                "expected_local_playlist_version": import_result["playlist"]["playlist_version"],
                "expected_remote_snapshot_checksum": remote["checksum"],
            },
        )
    )
    operation = apply_result["sync_apply"]["operation"]
    assert operation["status"] in {"failed", "partial"}


@pytest.mark.e2e
def test_e2e_sync_conflict_resolve_round_trip(e2e_harness: E2EHarness) -> None:
    """Scenario: sync.conflicts.resolve"""
    e2e_harness.provider.managed_playlist_repository().upsert(
        ManagedPlaylistDetail(
            summary=ManagedPlaylistSummary(
                local_playlist_id="local-conflict",
                name="Conflict Demo",
                provider_id=ProviderId.APPLE_MUSIC,
                track_count=1,
                sync_status="pending",
                provider_playlist_id="remote-conflict",
            ),
            tracks=(ManagedPlaylistTrack(local_track_id="t1", artist="Kygo", title="Firestone"),),
        )
    )
    remote = sample_remote_playlist_dict(checksum="conflict-checksum")
    remote["remote_playlist_id"] = "remote-conflict"

    plan = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.PLAN_SYNC.value,
            {
                "local_playlist_id": "local-conflict",
                "provider_id": "apple_music",
                "direction": "pull_from_provider",
                "sync_mode": "manual_resolve",
                "remote_playlist": remote,
            },
        )
    )
    conflicts = plan["sync_plan"]["conflicts"]
    assert conflicts

    resolved = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.RESOLVE_SYNC_CONFLICTS.value,
            {
                "local_playlist_id": "local-conflict",
                "provider_id": "apple_music",
                "direction": "pull_from_provider",
                "sync_mode": "manual_resolve",
                "remote_playlist": remote,
                "resolutions": [
                    {
                        "conflict_id": conflicts[0]["id"],
                        "strategy": conflicts[0].get("recommended_resolution") or "defer",
                    }
                ],
            },
        )
    )
    assert "plan_checksum" in resolved
