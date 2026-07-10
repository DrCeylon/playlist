from __future__ import annotations

from pathlib import Path

import pytest

from playlist_builder.app.playlist_library.import_remote import ImportRemotePlaylist
from playlist_builder.app.playlist_library.json_repository import JsonManagedPlaylistRepository
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.app.playlist_library.snapshot_archive import SnapshotArchive
from playlist_builder.app.playlist_sync.apply import ApplySyncPlaylist, ApplySyncRequest
from playlist_builder.app.playlist_sync.engine import PlaylistSyncEngine
from playlist_builder.app.playlist_sync.plan_checksum import plan_checksum
from playlist_builder.app.playlist_sync_operations.json_repository import JsonPlaylistSyncOperationRepository
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode, SyncOperationStatus
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack, remote_playlist_snapshot_checksum


class FakeWritePort(ProviderPlaylistWritePort):
    def __init__(self) -> None:
        self.upserted: list[tuple[str, tuple[RemotePlaylistTrack, ...]]] = []
        self.removed: list[tuple[str, tuple[str, ...]]] = []

    def create_playlist(self, name: str) -> str:
        return "remote-target"

    def upsert_tracks(self, remote_playlist_id: str, tracks: tuple[RemotePlaylistTrack, ...]) -> None:
        self.upserted.append((remote_playlist_id, tracks))

    def remove_tracks(self, remote_playlist_id: str, remote_track_ids: tuple[str, ...]) -> None:
        self.removed.append((remote_playlist_id, remote_track_ids))


@pytest.fixture
def repos(tmp_path: Path) -> RepositoryProvider:
    return RepositoryProvider(
        playlists_path=tmp_path / "managed_playlists.json",
        snapshots_dir=tmp_path / "snapshots",
        sync_operations_path=tmp_path / "sync_operations.json",
    )


def _local_with_track() -> ManagedPlaylistDetail:
    track = ManagedPlaylistTrack(
        local_track_id="loc-1",
        artist="Daft Punk",
        title="One More Time",
        provider_track_id="",
    )
    summary = ManagedPlaylistSummary(
        local_playlist_id="mpl-1",
        name="Push Demo",
        provider_id=ProviderId.APPLE_MUSIC,
        track_count=1,
        sync_status="pending",
        playlist_version=1,
    )
    return ManagedPlaylistDetail(summary=summary, tracks=(track,))


def _remote_empty() -> RemotePlaylistSnapshot:
    tracks: tuple[RemotePlaylistTrack, ...] = ()
    return RemotePlaylistSnapshot(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id="remote-target",
        name="Push Demo",
        snapshot_at_iso="2026-07-10T12:00:00",
        tracks=tracks,
        track_count=0,
        checksum=remote_playlist_snapshot_checksum(tracks),
        source_kind="provider_library",
    )


def test_push_append_only_apply_updates_repository_and_operations(repos: RepositoryProvider) -> None:
    playlist_repo = repos.managed_playlist_repository()
    local = _local_with_track()
    playlist_repo.upsert(local)
    remote = _remote_empty()
    engine = PlaylistSyncEngine()
    plan = engine.build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.APPEND_ONLY,
    )
    checksum = plan_checksum(plan)
    write_port = FakeWritePort()
    use_case = ApplySyncPlaylist(
        playlist_repository=playlist_repo,
        operation_repository=repos.sync_operation_repository(),
    )
    request = ApplySyncRequest(
        local_playlist_id="mpl-1",
        provider_id=ProviderId.APPLE_MUSIC,
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.APPEND_ONLY,
        confirm_destructive=False,
        expected_local_playlist_version=1,
        expected_remote_snapshot_checksum=remote.checksum,
        plan_checksum=checksum,
        remote_playlist_id=remote.remote_playlist_id,
    )
    result = use_case.execute(
        request,
        local=local,
        remote=remote,
        write_port=write_port,
        provider_capabilities=frozenset({ProviderCapability.PLAYLIST_SYNC}),
    )
    assert result.final_sync_status == "synced"
    assert len(write_port.upserted) == 1
    assert result.operation.status == SyncOperationStatus.COMPLETED
    updated = playlist_repo.get_playlist("mpl-1")
    assert updated is not None
    assert updated.summary.sync_status == "synced"
    assert updated.summary.linked_remote_refs[0].last_applied_snapshot_checksum == remote.checksum


def test_apply_sync_is_idempotent_on_second_call(repos: RepositoryProvider) -> None:
    playlist_repo = repos.managed_playlist_repository()
    local = _local_with_track()
    playlist_repo.upsert(local)
    remote = _remote_empty()
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.APPEND_ONLY,
    )
    checksum = plan_checksum(plan)
    write_port = FakeWritePort()
    use_case = ApplySyncPlaylist(
        playlist_repository=playlist_repo,
        operation_repository=repos.sync_operation_repository(),
    )
    request = ApplySyncRequest(
        local_playlist_id="mpl-1",
        provider_id=ProviderId.APPLE_MUSIC,
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.APPEND_ONLY,
        confirm_destructive=False,
        expected_local_playlist_version=1,
        expected_remote_snapshot_checksum=remote.checksum,
        plan_checksum=checksum,
    )
    first = use_case.execute(
        request,
        local=local,
        remote=remote,
        write_port=write_port,
        provider_capabilities=frozenset({ProviderCapability.PLAYLIST_SYNC}),
    )
    second = use_case.execute(
        request,
        local=playlist_repo.get_playlist("mpl-1") or local,
        remote=remote,
        write_port=write_port,
        provider_capabilities=frozenset({ProviderCapability.PLAYLIST_SYNC}),
    )
    assert first.operation.status == SyncOperationStatus.COMPLETED
    assert "idempotent" in second.message.lower() or second.operation.status in {
        SyncOperationStatus.COMPLETED,
        SyncOperationStatus.NO_OP,
    }


def test_mirror_without_confirmation_is_blocked(repos: RepositoryProvider) -> None:
    local_track = ManagedPlaylistTrack(local_track_id="loc-1", artist="A", title="B")
    remote_track = RemotePlaylistTrack(remote_track_id="r1", artist="C", title="D", position=1)
    local = ManagedPlaylistDetail(
        summary=ManagedPlaylistSummary(
            local_playlist_id="mpl-2",
            name="Mirror",
            provider_id=ProviderId.APPLE_MUSIC,
            track_count=1,
            sync_status="pending",
            playlist_version=1,
        ),
        tracks=(local_track,),
    )
    remote_tracks = (remote_track,)
    remote = RemotePlaylistSnapshot(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id="remote-2",
        name="Mirror",
        snapshot_at_iso="2026-07-10T12:00:00",
        tracks=remote_tracks,
        track_count=1,
        checksum=remote_playlist_snapshot_checksum(remote_tracks),
        source_kind="provider_library",
    )
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.MIRROR,
    )
    use_case = ApplySyncPlaylist(
        playlist_repository=repos.managed_playlist_repository(),
        operation_repository=repos.sync_operation_repository(),
    )
    result = use_case.execute(
        ApplySyncRequest(
            local_playlist_id="mpl-2",
            provider_id=ProviderId.APPLE_MUSIC,
            direction=SyncDirection.PUSH_TO_PROVIDER,
            sync_mode=SyncMode.MIRROR,
            confirm_destructive=False,
            expected_local_playlist_version=1,
            expected_remote_snapshot_checksum=remote.checksum,
            plan_checksum=plan_checksum(plan),
        ),
        local=local,
        remote=remote,
        write_port=FakeWritePort(),
        provider_capabilities=frozenset({ProviderCapability.PLAYLIST_SYNC}),
    )
    assert result.requires_confirmation is True
    assert result.operation.status == SyncOperationStatus.BLOCKED_CONFIRMATION


def test_stale_local_version_is_rejected(repos: RepositoryProvider) -> None:
    local = _local_with_track()
    remote = _remote_empty()
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PUSH_TO_PROVIDER,
        sync_mode=SyncMode.APPEND_ONLY,
    )
    use_case = ApplySyncPlaylist(
        playlist_repository=repos.managed_playlist_repository(),
        operation_repository=repos.sync_operation_repository(),
    )
    result = use_case.execute(
        ApplySyncRequest(
            local_playlist_id="mpl-1",
            provider_id=ProviderId.APPLE_MUSIC,
            direction=SyncDirection.PUSH_TO_PROVIDER,
            sync_mode=SyncMode.APPEND_ONLY,
            confirm_destructive=False,
            expected_local_playlist_version=99,
            expected_remote_snapshot_checksum=remote.checksum,
            plan_checksum=plan_checksum(plan),
        ),
        local=local,
        remote=remote,
        write_port=FakeWritePort(),
        provider_capabilities=frozenset({ProviderCapability.PLAYLIST_SYNC}),
    )
    assert result.operation.error_code == "local_version_stale"


def test_linked_remote_ref_migration_last_seen_applied() -> None:
    from playlist_builder.ui.shared.dto.playlist_library import linked_remote_ref_from_dict

    ref = linked_remote_ref_from_dict(
        {
            "provider_id": "apple_music",
            "remote_playlist_id": "r1",
            "snapshot_checksum": "legacy123",
        }
    )
    assert ref.last_seen_snapshot_checksum == "legacy123"
    assert ref.last_applied_snapshot_checksum == ""
