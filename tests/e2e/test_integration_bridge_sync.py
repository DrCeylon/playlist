from __future__ import annotations

import json

import pytest

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.bridge import BridgeCommand
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
from tests.e2e.harness import E2EHarness, FakeWritePort, build_e2e_harness, sample_remote_playlist_dict


def _import_and_plan_append(harness: E2EHarness, *, checksum: str = "idem-bridge-01") -> tuple[dict, dict, dict]:
    imported = harness.last_result(
        harness.call(
            BridgeCommand.IMPORT_REMOTE_PLAYLIST.value,
            {"remote_playlist": sample_remote_playlist_dict(checksum=checksum)},
        )
    )
    local_id = imported["playlist"]["local_playlist_id"]
    remote = sample_remote_playlist_dict(checksum=checksum)
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
    return imported, plan, remote


@pytest.mark.integration
def test_integration_apply_sync_idempotent_via_bridge(e2e_harness: E2EHarness) -> None:
    """Bridge apply_sync twice with same plan — second call is idempotent."""
    imported, plan, remote = _import_and_plan_append(e2e_harness)
    local_id = imported["playlist"]["local_playlist_id"]
    params = {
        "local_playlist_id": local_id,
        "provider_id": "apple_music",
        "direction": "push_to_provider",
        "sync_mode": "append_only",
        "remote_playlist": remote,
        "plan_checksum": plan["plan_checksum"],
        "expected_local_playlist_version": imported["playlist"]["playlist_version"],
        "expected_remote_snapshot_checksum": remote["checksum"],
        "confirm_destructive": False,
    }
    first = e2e_harness.sync_apply(e2e_harness.call(BridgeCommand.APPLY_SYNC.value, params, request_id="apply-1"))
    second = e2e_harness.sync_apply(e2e_harness.call(BridgeCommand.APPLY_SYNC.value, params, request_id="apply-2"))
    assert first["final_sync_status"] == "synced"
    assert second["operation"]["status"] in {"completed", "no_op"}
    assert "idempotent" in second.get("message", "").lower() or second["operation"]["status"] == "no_op"


@pytest.mark.integration
def test_integration_stale_plan_checksum_rejected_via_bridge(e2e_harness: E2EHarness) -> None:
    imported, plan, remote = _import_and_plan_append(e2e_harness, checksum="stale-plan-01")
    apply = e2e_harness.sync_apply(
        e2e_harness.call(
            BridgeCommand.APPLY_SYNC.value,
            {
                "local_playlist_id": imported["playlist"]["local_playlist_id"],
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "append_only",
                "remote_playlist": remote,
                "plan_checksum": "deadbeef" * 4,
                "expected_local_playlist_version": imported["playlist"]["playlist_version"],
                "expected_remote_snapshot_checksum": remote["checksum"],
            },
        )
    )
    assert apply["operation"]["error_code"] == "plan_checksum_mismatch"
    assert e2e_harness.settings.sync_operations_path.exists()


@pytest.mark.integration
def test_integration_stale_local_version_rejected_via_bridge(e2e_harness: E2EHarness) -> None:
    imported, plan, remote = _import_and_plan_append(e2e_harness, checksum="stale-local-01")
    apply = e2e_harness.sync_apply(
        e2e_harness.call(
            BridgeCommand.APPLY_SYNC.value,
            {
                "local_playlist_id": imported["playlist"]["local_playlist_id"],
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "append_only",
                "remote_playlist": remote,
                "plan_checksum": plan["plan_checksum"],
                "expected_local_playlist_version": 99,
                "expected_remote_snapshot_checksum": remote["checksum"],
            },
        )
    )
    assert apply["operation"]["error_code"] == "local_version_stale"


@pytest.mark.integration
def test_integration_mirror_blocked_without_confirmation_via_bridge(e2e_harness: E2EHarness) -> None:
    """Mirror with destructive diff requires confirm_destructive — not claimed as supported apply."""
    e2e_harness.provider.managed_playlist_repository().upsert(
        ManagedPlaylistDetail(
            summary=ManagedPlaylistSummary(
                local_playlist_id="mirror-local",
                name="Mirror Local",
                provider_id=ProviderId.APPLE_MUSIC,
                track_count=1,
                sync_status="pending",
                playlist_version=1,
                provider_playlist_id="mirror-remote",
            ),
            tracks=(ManagedPlaylistTrack(local_track_id="t1", artist="A", title="Local Track"),),
        )
    )
    remote = sample_remote_playlist_dict(checksum="mirror-checksum-01")
    remote["remote_playlist_id"] = "mirror-remote"
    remote["tracks"] = [
        {
            "remote_track_id": "r-remote",
            "artist": "B",
            "title": "Remote Only",
            "position": 0,
        },
    ]
    plan = e2e_harness.last_result(
        e2e_harness.call(
            BridgeCommand.PLAN_SYNC.value,
            {
                "local_playlist_id": "mirror-local",
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "mirror",
                "remote_playlist": remote,
            },
        )
    )
    apply = e2e_harness.sync_apply(
        e2e_harness.call(
            BridgeCommand.APPLY_SYNC.value,
            {
                "local_playlist_id": "mirror-local",
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "mirror",
                "remote_playlist": remote,
                "plan_checksum": plan["plan_checksum"],
                "expected_local_playlist_version": 1,
                "expected_remote_snapshot_checksum": remote["checksum"],
                "confirm_destructive": False,
            },
        )
    )
    assert apply["requires_confirmation"] is True
    assert apply["operation"]["status"] == "blocked_confirmation"


@pytest.mark.integration
def test_integration_partial_sync_write_failure_records_operation(tmp_path) -> None:
    harness = build_e2e_harness(tmp_path, write_port=FakeWritePort(fail_on_call=1))
    imported, plan, remote = _import_and_plan_append(harness, checksum="partial-01")
    apply = harness.sync_apply(
        harness.call(
            BridgeCommand.APPLY_SYNC.value,
            {
                "local_playlist_id": imported["playlist"]["local_playlist_id"],
                "provider_id": "apple_music",
                "direction": "push_to_provider",
                "sync_mode": "append_only",
                "remote_playlist": remote,
                "plan_checksum": plan["plan_checksum"],
                "expected_local_playlist_version": imported["playlist"]["playlist_version"],
                "expected_remote_snapshot_checksum": remote["checksum"],
            },
        )
    )
    assert apply["operation"]["status"] in {"failed", "partial"}
    journal = json.loads(harness.settings.sync_operations_path.read_text(encoding="utf-8"))
    assert journal["operations"]
    assert journal["operations"][0]["status"] in {"failed", "partial"}


@pytest.mark.integration
def test_integration_sync_conflict_resolve_round_trip(e2e_harness: E2EHarness) -> None:
    """plan_sync manual_resolve → resolve_sync_conflicts via bridge (repo seeded directly)."""
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
