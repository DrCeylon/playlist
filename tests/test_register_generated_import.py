from __future__ import annotations

from pathlib import Path

import pytest

from playlist_builder.app.bridge_runtime.backend import RuntimeEngineBridgeBackend
from playlist_builder.app.bridge_runtime.playlist_sync_plan import plan_sync
from playlist_builder.app.factory import build_app_context
from playlist_builder.app.playlist_library.migration import HistoryToRepositoryMigration
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.app.playlist_library.register_generated_import import RegisterGeneratedImport
from playlist_builder.app.playlist_library.remote_link_resolver import (
    ProviderRemotePlaylistLinker,
    RemoteLinkStatus,
)
from playlist_builder.app.settings import AppSettings
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.ui.bridge.commands import ImportPlaylistResult
from playlist_builder.ui.shared.dto.enums import ImportPhase, ImportTrackStatus
from playlist_builder.ui.shared.dto.import_state import ImportResultState, ImportTrackOutcome
from playlist_builder.ui.shared.dto.playlist_library import PlaylistOrigin
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import (
    RemotePlaylist,
    RemotePlaylistSnapshot,
    RemotePlaylistTrack,
    remote_playlist_snapshot_checksum,
)
from playlist_builder.ui.shared.history import SessionHistoryService, SessionHistoryRepository


class _FakeReadPort(ProviderPlaylistReadPort):
    def __init__(
        self,
        playlists: tuple[RemotePlaylist, ...],
        snapshots: dict[str, RemotePlaylistSnapshot] | None = None,
    ) -> None:
        self._playlists = playlists
        self._snapshots = snapshots or {}

    def list_playlists(self, *, account_id: str | None = None) -> tuple[RemotePlaylist, ...]:
        del account_id
        return self._playlists

    def get_playlist(self, remote_playlist_id: str) -> RemotePlaylistSnapshot:
        snapshot = self._snapshots.get(remote_playlist_id)
        if snapshot is None:
            raise ValueError(f"unknown playlist {remote_playlist_id}")
        return snapshot


def _provider(tmp_path: Path) -> RepositoryProvider:
    return RepositoryProvider(
        playlists_path=tmp_path / "managed_playlists.json",
        snapshots_dir=tmp_path / "snapshots",
    )


def _import_result(*, phase: ImportPhase = ImportPhase.PARTIAL_SUCCESS) -> ImportResultState:
    return ImportResultState(
        playlist_name="Pool Party",
        outcomes=(
            ImportTrackOutcome("Artist A", "Track A", "Main", ImportTrackStatus.ADDED),
            ImportTrackOutcome("Artist B", "Track B", "Main", ImportTrackStatus.NOT_FOUND),
        ),
        phase=phase,
    )


def _remote_snapshot(remote_id: str = "apple-pl-42") -> RemotePlaylistSnapshot:
    tracks = (
        RemotePlaylistTrack(remote_track_id="t1", artist="Artist A", title="Track A", position=0),
        RemotePlaylistTrack(remote_track_id="t2", artist="Artist B", title="Track B", position=1),
    )
    return RemotePlaylistSnapshot(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id=remote_id,
        name="Pool Party",
        snapshot_at_iso="2026-07-11T10:00:00Z",
        tracks=tracks,
        track_count=len(tracks),
        checksum=remote_playlist_snapshot_checksum(tracks),
        source_kind="provider_library",
    )


def test_register_generated_import_persists_linked_playlist(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    snapshot = _remote_snapshot()
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="apple-pl-42",
                name="Pool Party",
                track_count=2,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"apple-pl-42": snapshot},
    )
    use_case = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    )
    detail = use_case.execute(
        history_session_id="sess-post-import",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Pool Party",
        import_result=_import_result(),
        read_port=read_port,
    )
    assert detail is not None
    assert detail.summary.local_playlist_id == "hist-sess-post-import"
    assert detail.summary.provider_playlist_id == "apple-pl-42"
    assert detail.summary.origin == PlaylistOrigin.GENERATED.value
    assert len(detail.summary.linked_remote_refs) == 1
    assert detail.summary.linked_remote_refs[0].remote_playlist_id == "apple-pl-42"
    assert detail.summary.sync_status == "partial"
    assert len(detail.tracks) == 2
    assert detail.tracks[0].mapping_status == "matched"
    assert detail.tracks[1].mapping_status == "missing_on_provider"


def test_register_generated_import_retry_updates_same_playlist(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="apple-pl-42",
                name="Pool Party",
                track_count=2,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"apple-pl-42": _remote_snapshot()},
    )
    use_case = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    )
    use_case.execute(
        history_session_id="sess-retry",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Pool Party",
        import_result=_import_result(),
        read_port=read_port,
    )
    retry_result = ImportResultState(
        playlist_name="Pool Party",
        outcomes=(
            ImportTrackOutcome("Artist A", "Track A", "Main", ImportTrackStatus.ADDED),
            ImportTrackOutcome("Artist B", "Track B", "Main", ImportTrackStatus.ADDED),
        ),
        phase=ImportPhase.COMPLETED,
    )
    updated = use_case.execute(
        history_session_id="sess-retry",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Pool Party",
        import_result=retry_result,
        read_port=read_port,
    )
    assert updated is not None
    assert updated.summary.playlist_version == 2
    assert updated.summary.sync_status == "synced"
    assert updated.tracks[1].mapping_status == "matched"
    playlists = provider.managed_playlist_repository().list_playlists()
    assert len(playlists) == 1


def test_lazy_migration_skips_when_register_already_persisted(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="apple-pl-42",
                name="Pool Party",
                track_count=2,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"apple-pl-42": _remote_snapshot()},
    )
    RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    ).execute(
        history_session_id="sess-1",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Pool Party",
        import_result=_import_result(phase=ImportPhase.COMPLETED),
        read_port=read_port,
    )
    migration = HistoryToRepositoryMigration(provider.managed_playlist_repository())
    migration.ensure_migrated(
        (
            {
                "session_id": "sess-1",
                "playlist_name": "Pool Party",
                "provider_id": "apple_music",
                "status": "imported",
                "track_count": 2,
                "started_at_iso": "2026-07-01T10:00:00",
                "finished_at_iso": "2026-07-01T10:05:00",
                "import_result": {
                    "outcomes": [
                        {"artist": "Artist A", "title": "Track A", "section": "Main", "status": "added"},
                    ],
                },
            },
        )
    )
    detail = provider.managed_playlist_repository().get_playlist("hist-sess-1")
    assert detail is not None
    assert detail.summary.provider_playlist_id == "apple-pl-42"
    assert len(provider.managed_playlist_repository().list_playlists()) == 1


def test_remote_link_resolver_rejects_ambiguous_names() -> None:
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="pl-1",
                name="Duplicates",
                track_count=1,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="pl-2",
                name="Duplicates",
                track_count=1,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        )
    )
    link = ProviderRemotePlaylistLinker().resolve(
        read_port,
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Duplicates",
    )
    assert link.status == RemoteLinkStatus.AMBIGUOUS
    assert link.remote_playlist_id == ""


def test_register_without_remote_match_marks_not_linked(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    read_port = _FakeReadPort(playlists=())
    detail = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    ).execute(
        history_session_id="sess-unlinked",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Missing Remote",
        import_result=_import_result(phase=ImportPhase.COMPLETED),
        read_port=read_port,
    )
    assert detail is not None
    assert detail.summary.sync_status == "not_linked"
    assert detail.summary.provider_playlist_id == ""
    assert detail.summary.linked_remote_refs == ()


def test_plan_sync_succeeds_with_import_registered_link(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    snapshot = _remote_snapshot("remote-sync-1")
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-sync-1",
                name="Pool Party",
                track_count=2,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"remote-sync-1": snapshot},
    )
    detail = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    ).execute(
        history_session_id="sess-sync",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Pool Party",
        import_result=_import_result(phase=ImportPhase.COMPLETED),
        read_port=read_port,
    )
    assert detail is not None

    class _Gateway:
        @property
        def provider_id(self) -> ProviderId:
            return ProviderId.APPLE_MUSIC

        @property
        def capabilities(self) -> frozenset[ProviderCapability]:
            return frozenset({ProviderCapability.PLAYLIST_SYNC})

        @property
        def playlist_read(self) -> ProviderPlaylistReadPort:
            return read_port

    registry = ProviderGatewayRegistry()
    registry.register(_Gateway())  # type: ignore[arg-type]

    plan = plan_sync(
        registry,
        local_detail=detail,
        remote_snapshot=None,
        provider_id=ProviderId.APPLE_MUSIC,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.MANUAL_RESOLVE,
        remote_playlist_id=detail.summary.provider_playlist_id,
    )
    assert "sync_plan" in plan
    assert plan["sync_plan"]["remote_playlist_id"] == "remote-sync-1"


def test_post_import_journey_partial_success_retry_completed(tmp_path: Path) -> None:
    """Integration: partial_success → retry → completed leaves one linked managed playlist."""
    provider = _provider(tmp_path)
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-journey-1",
                name="Journey Mix",
                track_count=2,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"remote-journey-1": _remote_snapshot("remote-journey-1")},
    )
    use_case = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    )
    partial = ImportResultState(
        playlist_name="Journey Mix",
        outcomes=(
            ImportTrackOutcome("Artist A", "Track A", "Main", ImportTrackStatus.ADDED),
            ImportTrackOutcome("Artist B", "Track B", "Main", ImportTrackStatus.NOT_FOUND),
        ),
        phase=ImportPhase.PARTIAL_SUCCESS,
    )
    use_case.execute(
        history_session_id="sess-journey",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Journey Mix",
        import_result=partial,
        read_port=read_port,
    )
    completed = ImportResultState(
        playlist_name="Journey Mix",
        outcomes=(
            ImportTrackOutcome("Artist A", "Track A", "Main", ImportTrackStatus.ADDED),
            ImportTrackOutcome("Artist B", "Track B", "Main", ImportTrackStatus.ADDED),
        ),
        phase=ImportPhase.COMPLETED,
    )
    final = use_case.execute(
        history_session_id="sess-journey",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Journey Mix",
        import_result=completed,
        read_port=read_port,
    )
    assert final is not None
    repo = provider.managed_playlist_repository()
    playlists = repo.list_playlists()
    assert len(playlists) == 1
    assert final.summary.linked_remote_refs[0].remote_playlist_id == "remote-journey-1"
    assert final.summary.playlist_version == 2
    assert final.summary.sync_status == "synced"

    class _Gateway:
        @property
        def provider_id(self) -> ProviderId:
            return ProviderId.APPLE_MUSIC

        @property
        def capabilities(self) -> frozenset[ProviderCapability]:
            return frozenset({ProviderCapability.PLAYLIST_SYNC})

        @property
        def playlist_read(self) -> ProviderPlaylistReadPort:
            return read_port

    registry = ProviderGatewayRegistry()
    registry.register(_Gateway())  # type: ignore[arg-type]
    plan = plan_sync(
        registry,
        local_detail=final,
        remote_snapshot=None,
        provider_id=ProviderId.APPLE_MUSIC,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.MANUAL_RESOLVE,
        remote_playlist_id=final.summary.provider_playlist_id,
    )
    assert plan["sync_plan"]["remote_playlist_id"] == "remote-journey-1"


def test_backend_attach_history_registers_managed_playlist(tmp_path: Path) -> None:
    context = build_app_context(
        AppSettings(
            managed_playlists_path=tmp_path / "backend-managed_playlists.json",
            playlist_snapshots_dir=tmp_path / "backend-snapshots",
        )
    )
    backend = RuntimeEngineBridgeBackend(context)
    history_repo = SessionHistoryRepository(tmp_path / "backend-history.json")
    backend._history = SessionHistoryService(history_repo)
    backend._repository_provider = RepositoryProvider(
        playlists_path=tmp_path / "backend-managed_playlists.json",
        snapshots_dir=tmp_path / "backend-snapshots",
    )
    backend._playlist_migration = HistoryToRepositoryMigration(
        backend._repository_provider.managed_playlist_repository()
    )

    class _Gateway:
        @property
        def provider_id(self) -> ProviderId:
            return ProviderId.APPLE_MUSIC

        @property
        def capabilities(self) -> frozenset[ProviderCapability]:
            return frozenset({ProviderCapability.PLAYLIST_SYNC})

        @property
        def playlist_read(self) -> ProviderPlaylistReadPort:
            return _FakeReadPort(
                playlists=(
                    RemotePlaylist(
                        provider_id=ProviderId.APPLE_MUSIC,
                        remote_playlist_id="remote-backend-1",
                        name="Backend Flow",
                        track_count=1,
                        is_public=False,
                        owner_label="Apple Music",
                        snapshot_at_iso="2026-07-11T10:00:00Z",
                    ),
                ),
                snapshots={"remote-backend-1": _remote_snapshot("remote-backend-1")},
            )

    fake_gateway = _Gateway()
    context.registry._gateways[ProviderId.APPLE_MUSIC] = fake_gateway  # type: ignore[assignment]

    created = backend._history.create_generation_session(
        request_id="gen-1",
        playlist_name="Backend Flow",
        provider_id=ProviderId.APPLE_MUSIC,
        generation_request={"name": "Backend Flow"},
        generation_result={"playlist_name": "Backend Flow"},
        track_count=1,
    )
    result = ImportResultState(
        playlist_name="Backend Flow",
        outcomes=(ImportTrackOutcome("A", "B", "Main", ImportTrackStatus.ADDED),),
        phase=ImportPhase.COMPLETED,
    )
    attached = backend._attach_history_import_result(
        ImportPlaylistResult(import_result=result, history_session_id=created.session_id),
        created.session_id,
        provider_id=ProviderId.APPLE_MUSIC,
    )
    playlists = backend._repository_provider.managed_playlist_repository().list_playlists()
    assert len(playlists) == 1
    assert playlists[0].summary.local_playlist_id == f"hist-{created.session_id}"
    assert playlists[0].summary.provider_playlist_id == "remote-backend-1"
    assert attached.history_session_id == created.session_id
