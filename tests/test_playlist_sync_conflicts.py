from __future__ import annotations

from playlist_builder.app.playlist_sync.conflict_resolver import ConflictResolution, PlaylistConflictResolver
from playlist_builder.app.playlist_sync.engine import PlaylistSyncEngine
from playlist_builder.app.playlist_sync.resolve_conflicts import ResolveSyncConflicts, ResolveSyncConflictsRequest
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_library import LinkedRemoteRef, ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack, remote_playlist_snapshot_checksum
from playlist_builder.ui.shared.dto.sync_conflict import ConflictKind, ConflictResolutionStrategy


def _local(**kwargs: object) -> ManagedPlaylistDetail:
    tracks = kwargs.pop("tracks", ())
    linked_refs = kwargs.pop("linked_remote_refs", ())
    summary = ManagedPlaylistSummary(
        local_playlist_id="local-1",
        name=str(kwargs.get("name", "Demo")),
        provider_id=ProviderId.APPLE_MUSIC,
        track_count=len(tracks),  # type: ignore[arg-type]
        sync_status="pending",
        playlist_version=int(kwargs.get("playlist_version", 1)),
        linked_remote_refs=linked_refs,  # type: ignore[arg-type]
    )
    return ManagedPlaylistDetail(summary=summary, tracks=tracks)  # type: ignore[arg-type]


def _remote(tracks: tuple[RemotePlaylistTrack, ...], **kwargs: object) -> RemotePlaylistSnapshot:
    checksum = remote_playlist_snapshot_checksum(tracks)
    return RemotePlaylistSnapshot(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id=str(kwargs.get("remote_playlist_id", "remote-1")),
        name=str(kwargs.get("name", "Demo")),
        snapshot_at_iso="2026-07-10T12:00:00Z",
        tracks=tracks,
        track_count=len(tracks),
        checksum=checksum,
        source_kind="provider_library",
    )


def test_enriched_conflict_contains_resolution_options() -> None:
    local = _local(
        tracks=(
            ManagedPlaylistTrack(local_track_id="1", artist="Dup", title="Song"),
            ManagedPlaylistTrack(local_track_id="2", artist="Dup", title="Song"),
        )
    )
    remote = _remote(())
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.DRY_RUN,
    )
    assert plan.conflicts
    conflict = next(item for item in plan.conflicts if "dup" in item.id)
    payload = conflict.to_dict()
    assert "duplicate" in payload["kind"]
    assert payload["available_resolutions"]
    assert payload["recommended_resolution"]


def test_manual_resolve_metadata_produces_conflict_not_map_action() -> None:
    local = _local(
        tracks=(ManagedPlaylistTrack(local_track_id="loc-1", artist="Kygo", title="Firestone", provider_track_id="old"),),
        linked_remote_refs=(
            LinkedRemoteRef(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-1",
                snapshot_checksum="abc",
                last_seen_snapshot_checksum="abc",
            ),
        ),
    )
    remote = _remote(
        (RemotePlaylistTrack(remote_track_id="new", artist="Kygo", title="Firestone", album="Album", position=1),)
    )
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.MANUAL_RESOLVE,
    )
    assert any(conflict.kind == ConflictKind.METADATA_MISMATCH.value for conflict in plan.conflicts)
    assert not any(action.kind.value == "map_track" for action in plan.actions)


def test_resolve_keep_local_removes_conflicting_actions() -> None:
    local = _local(
        tracks=(ManagedPlaylistTrack(local_track_id="loc-1", artist="Kygo", title="Firestone", provider_track_id="old"),),
        linked_remote_refs=(
            LinkedRemoteRef(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-1",
                snapshot_checksum="abc",
                last_seen_snapshot_checksum="abc",
            ),
        ),
    )
    remote = _remote(
        (RemotePlaylistTrack(remote_track_id="new", artist="Kygo", title="Firestone", album="Album", position=1),)
    )
    baseline = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.MANUAL_RESOLVE,
    )
    conflict = next(item for item in baseline.conflicts if item.kind == ConflictKind.METADATA_MISMATCH.value)
    resolved = PlaylistConflictResolver().resolve(
        baseline,
        (ConflictResolution(conflict_id=conflict.id, strategy=ConflictResolutionStrategy.KEEP_LOCAL),),
    )
    assert conflict.id not in {item.id for item in resolved.conflicts}
    assert not any(action.kind.value == "map_track" for action in resolved.actions)


def test_resolve_merge_adds_map_track_action() -> None:
    local = _local(
        tracks=(ManagedPlaylistTrack(local_track_id="loc-1", artist="Kygo", title="Firestone", provider_track_id="old"),),
        linked_remote_refs=(
            LinkedRemoteRef(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-1",
                snapshot_checksum="abc",
                last_seen_snapshot_checksum="abc",
            ),
        ),
    )
    remote = _remote(
        (RemotePlaylistTrack(remote_track_id="new", artist="Kygo", title="Firestone", album="Album", position=1),)
    )
    baseline = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.MANUAL_RESOLVE,
    )
    conflict = next(item for item in baseline.conflicts if item.kind == ConflictKind.METADATA_MISMATCH.value)
    resolved = PlaylistConflictResolver().resolve(
        baseline,
        (ConflictResolution(conflict_id=conflict.id, strategy=ConflictResolutionStrategy.MERGE),),
    )
    assert conflict.id not in {item.id for item in resolved.conflicts}
    assert any(action.kind.value == "map_track" for action in resolved.actions)


def test_resolve_sync_conflicts_use_case_returns_new_checksum() -> None:
    local = _local(
        tracks=(ManagedPlaylistTrack(local_track_id="loc-1", artist="Kygo", title="Firestone", provider_track_id="old"),),
        linked_remote_refs=(
            LinkedRemoteRef(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-1",
                snapshot_checksum="abc",
                last_seen_snapshot_checksum="abc",
            ),
        ),
    )
    remote = _remote(
        (RemotePlaylistTrack(remote_track_id="new", artist="Kygo", title="Firestone", album="Album", position=1),)
    )
    baseline = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.MANUAL_RESOLVE,
    )
    conflict = next(item for item in baseline.conflicts if item.kind == ConflictKind.METADATA_MISMATCH.value)
    result = ResolveSyncConflicts().execute(
        ResolveSyncConflictsRequest(
            local_playlist_id="local-1",
            provider_id=ProviderId.APPLE_MUSIC.value,
            direction=SyncDirection.PULL_FROM_PROVIDER,
            sync_mode=SyncMode.MANUAL_RESOLVE,
            remote_playlist_id="remote-1",
            resolutions=(ConflictResolution(conflict_id=conflict.id, strategy=ConflictResolutionStrategy.MERGE),),
        ),
        local=local,
        remote=remote,
    )
    assert result.plan_checksum
    assert result.remaining_conflicts == 0


def test_defer_keeps_conflict_in_plan() -> None:
    local = _local(
        tracks=(
            ManagedPlaylistTrack(local_track_id="1", artist="Dup", title="Song"),
            ManagedPlaylistTrack(local_track_id="2", artist="Dup", title="Song"),
        )
    )
    remote = _remote(())
    baseline = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.MANUAL_RESOLVE,
    )
    conflict = baseline.conflicts[0]
    resolved = PlaylistConflictResolver().resolve(
        baseline,
        (ConflictResolution(conflict_id=conflict.id, strategy=ConflictResolutionStrategy.DEFER),),
    )
    assert any(item.id == conflict.id for item in resolved.conflicts)


def test_conflict_serialization_round_trip() -> None:
    from playlist_builder.ui.shared.dto.playlist_library import playlist_sync_conflict_from_dict

    payload = {
        "id": "meta-1",
        "track_key": "kygo::firestone",
        "kind": "metadata_mismatch",
        "message": "test",
        "scope": "track",
        "severity": "warning",
        "available_resolutions": ["keep_local", "keep_remote", "merge", "defer"],
        "recommended_resolution": "defer",
    }
    conflict = playlist_sync_conflict_from_dict(payload)
    round_trip = conflict.to_dict()
    assert round_trip["kind"] == "metadata_mismatch"
    assert "available_resolutions" in round_trip
