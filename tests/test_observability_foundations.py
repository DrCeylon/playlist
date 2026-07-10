from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from playlist_builder.observability import (
    EventCategory,
    NoOpObservabilityRecorder,
    ObservabilityBus,
    ObservabilityRecorder,
    ResonanceEvent,
    ResonanceEventKind,
    export_observability_bundle,
    get_default_bus,
    reset_default_bus,
)

if TYPE_CHECKING:
    from playlist_builder.app.playlist_library.provider import RepositoryProvider


def test_resonance_event_to_dict_roundtrip_fields() -> None:
    event = ResonanceEvent.now(
        kind=ResonanceEventKind.SYNC_PLAN_COMPLETED,
        category=EventCategory.SYNC,
        message="plan ok",
        local_playlist_id="mpl-1",
        provider_id="apple_music",
        duration_ms=12,
        success=True,
        attributes=(("actions_total", "3"),),
    )
    payload = event.to_dict()
    assert payload["kind"] == "sync.plan.completed"
    assert payload["category"] == "sync"
    assert payload["local_playlist_id"] == "mpl-1"
    assert payload["provider_id"] == "apple_music"
    assert payload["duration_ms"] == 12
    assert payload["attributes"]["actions_total"] == "3"
    assert payload["correlation_id"]


def test_bus_retains_events_and_filters_by_category() -> None:
    bus = ObservabilityBus(max_events=10)
    recorder = ObservabilityRecorder(bus=bus)
    recorder.record_sync_plan_completed(
        local_playlist_id="mpl-1",
        provider_id="apple_music",
        duration_ms=5,
        actions_total=1,
        conflicts_total=0,
    )
    bus.emit(
        ResonanceEvent.now(
            kind=ResonanceEventKind.HEALTH_CHECK,
            category=EventCategory.SYSTEM,
            message="ok",
            success=True,
        )
    )
    sync_events = bus.recent_events(category=EventCategory.SYNC)
    assert len(sync_events) == 1
    assert sync_events[0].kind == ResonanceEventKind.SYNC_PLAN_COMPLETED
    assert bus.event_count() == 2


def test_metrics_aggregate_success_failure_and_duration() -> None:
    bus = ObservabilityBus()
    recorder = ObservabilityRecorder(bus=bus)
    recorder.record_sync_apply_completed(
        local_playlist_id="mpl-1",
        provider_id="apple_music",
        operation_id="op-1",
        duration_ms=100,
        status="completed",
        actions_completed=2,
        actions_failed=0,
        correlation_id="cid-1",
    )
    recorder.record_sync_apply_failed(
        local_playlist_id="mpl-2",
        provider_id="apple_music",
        operation_id="op-2",
        duration_ms=50,
        error_message="boom",
        correlation_id="cid-2",
    )
    summary = bus.metrics.summary()
    assert summary["event_counts"]["sync.apply.completed"] == 1
    assert summary["failure_counts"]["sync.apply.failed"] == 1
    assert summary["average_duration_ms"]["sync.apply.completed"] == 100


def test_sync_timeline_filters_by_playlist() -> None:
    bus = ObservabilityBus()
    recorder = ObservabilityRecorder(bus=bus)
    recorder.record_sync_plan_completed(
        local_playlist_id="mpl-a",
        provider_id="apple_music",
        duration_ms=1,
        actions_total=0,
        conflicts_total=0,
    )
    recorder.record_sync_plan_completed(
        local_playlist_id="mpl-b",
        provider_id="apple_music",
        duration_ms=2,
        actions_total=0,
        conflicts_total=0,
    )
    timeline = bus.sync_timeline(local_playlist_id="mpl-a")
    assert len(timeline) == 1
    assert timeline[0]["local_playlist_id"] == "mpl-a"


def test_noop_recorder_does_not_emit() -> None:
    bus = ObservabilityBus()
    noop = NoOpObservabilityRecorder()
    noop.record_sync_plan_completed(
        local_playlist_id="mpl-1",
        provider_id="apple_music",
        duration_ms=1,
        actions_total=0,
        conflicts_total=0,
    )
    assert bus.event_count() == 0


def test_export_bundle_contains_expected_sections() -> None:
    reset_default_bus()
    bus = get_default_bus()
    ObservabilityRecorder(bus=bus).record_sync_plan_completed(
        local_playlist_id="mpl-1",
        provider_id="apple_music",
        duration_ms=3,
        actions_total=1,
        conflicts_total=0,
    )
    bundle = export_observability_bundle(bus=bus, health={"status": "ok"})
    assert bundle["api_version"] == "1.0.0"
    assert bundle["health"]["status"] == "ok"
    assert bundle["event_count"] >= 1
    assert bundle["recent_events"]
    assert bundle["sync_timeline"]


def test_observability_package_has_no_integration_imports() -> None:
    root = Path("playlist_builder/observability")
    forbidden = "playlist_builder.integration"
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and forbidden in node.module:
                raise AssertionError(f"{path} imports {node.module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if forbidden in alias.name:
                        raise AssertionError(f"{path} imports {alias.name}")


def test_apply_sync_emits_typed_events(repos) -> None:
    from playlist_builder.app.playlist_library.provider import RepositoryProvider
    from playlist_builder.app.playlist_sync.apply import ApplySyncPlaylist, ApplySyncRequest
    from playlist_builder.app.playlist_sync.engine import PlaylistSyncEngine
    from playlist_builder.app.playlist_sync.plan_checksum import plan_checksum
    from playlist_builder.canonical.enums import ProviderCapability, ProviderId
    from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
    from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
    from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
    from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack, remote_playlist_snapshot_checksum

    class FakeWritePort(ProviderPlaylistWritePort):
        def create_playlist(self, name: str) -> str:
            return "remote-target"

        def upsert_tracks(self, remote_playlist_id: str, tracks: tuple[RemotePlaylistTrack, ...]) -> None:
            return None

        def remove_tracks(self, remote_playlist_id: str, remote_track_ids: tuple[str, ...]) -> None:
            return None

    reset_default_bus()
    bus = ObservabilityBus()
    playlist_repo = repos.managed_playlist_repository()
    track = ManagedPlaylistTrack(
        local_track_id="loc-1",
        artist="Daft Punk",
        title="One More Time",
        provider_track_id="",
    )
    summary = ManagedPlaylistSummary(
        local_playlist_id="mpl-obs",
        name="Obs Demo",
        provider_id=ProviderId.APPLE_MUSIC,
        track_count=1,
        sync_status="pending",
        playlist_version=1,
    )
    local = ManagedPlaylistDetail(summary=summary, tracks=(track,))
    playlist_repo.upsert(local)
    tracks: tuple[RemotePlaylistTrack, ...] = ()
    remote = RemotePlaylistSnapshot(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id="remote-target",
        name="Obs Demo",
        snapshot_at_iso="2026-07-10T12:00:00",
        tracks=tracks,
        track_count=0,
        checksum=remote_playlist_snapshot_checksum(tracks),
        source_kind="provider_library",
    )
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.APPEND_ONLY,
    )
    use_case = ApplySyncPlaylist(
        playlist_repository=playlist_repo,
        operation_repository=repos.sync_operation_repository(),
        observability=ObservabilityRecorder(bus=bus),
    )
    result = use_case.execute(
        ApplySyncRequest(
            local_playlist_id="mpl-obs",
            provider_id=ProviderId.APPLE_MUSIC,
            direction=SyncDirection.PUSH_TO_PROVIDER,
            sync_mode=SyncMode.APPEND_ONLY,
            confirm_destructive=False,
            expected_local_playlist_version=1,
            expected_remote_snapshot_checksum=remote.checksum,
            plan_checksum=plan_checksum(plan),
            remote_playlist_id=remote.remote_playlist_id,
        ),
        local=local,
        remote=remote,
        write_port=FakeWritePort(),
        provider_capabilities=frozenset({ProviderCapability.PLAYLIST_SYNC}),
    )
    assert result.final_sync_status == "synced"
    kinds = {event.kind for event in bus.recent_events(category=EventCategory.SYNC)}
    assert ResonanceEventKind.SYNC_APPLY_STARTED in kinds
    assert ResonanceEventKind.SYNC_APPLY_COMPLETED in kinds


@pytest.fixture
def repos(tmp_path: Path):
    from playlist_builder.app.playlist_library.provider import RepositoryProvider

    return RepositoryProvider(
        playlists_path=tmp_path / "managed_playlists.json",
        snapshots_dir=tmp_path / "snapshots",
        sync_operations_path=tmp_path / "sync_operations.json",
    )
