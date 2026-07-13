from __future__ import annotations

from pathlib import Path

import pytest

from playlist_builder.app.playlist_library.linked_refs import merge_linked_remote_refs
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.app.playlist_library.register_generated_import import RegisterGeneratedImport
from playlist_builder.app.playlist_library.remote_link_resolver import RemoteLinkStatus, RemotePlaylistLinkResult
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.ui.shared.dto.enums import ImportPhase, ImportTrackStatus
from playlist_builder.ui.shared.dto.import_state import ImportResultState, ImportTrackOutcome
from playlist_builder.ui.shared.dto.playlist_library import (
    LinkedRemoteRef,
    ManagedPlaylistDetail,
    ManagedPlaylistSummary,
)
from playlist_builder.ui.shared.dto.remote_playlist import (
    RemotePlaylist,
    RemotePlaylistSnapshot,
    RemotePlaylistTrack,
    remote_playlist_snapshot_checksum,
)
from playlist_builder.ui.shared.playlist_ids import managed_local_playlist_id_from_history


class _FakeReadPort(ProviderPlaylistReadPort):
    def __init__(
        self,
        playlists: tuple[RemotePlaylist, ...],
        snapshots: dict[str, RemotePlaylistSnapshot] | None = None,
        *,
        list_error: BaseException | None = None,
        get_error_for: set[str] | None = None,
    ) -> None:
        self._playlists = playlists
        self._snapshots = snapshots or {}
        self._list_error = list_error
        self._get_error_for = get_error_for or set()

    def list_playlists(self, *, account_id: str | None = None) -> tuple[RemotePlaylist, ...]:
        del account_id
        if self._list_error is not None:
            raise self._list_error
        return self._playlists

    def get_playlist(self, remote_playlist_id: str) -> RemotePlaylistSnapshot:
        if remote_playlist_id in self._get_error_for:
            raise ValueError(f"snapshot unavailable for {remote_playlist_id}")
        snapshot = self._snapshots.get(remote_playlist_id)
        if snapshot is None:
            raise ValueError(f"unknown playlist {remote_playlist_id}")
        return snapshot


def _provider(tmp_path: Path) -> RepositoryProvider:
    return RepositoryProvider(
        playlists_path=tmp_path / "managed_playlists.json",
        snapshots_dir=tmp_path / "snapshots",
    )


def _apple_snapshot(remote_id: str, name: str = "Pool Party") -> RemotePlaylistSnapshot:
    tracks = (RemotePlaylistTrack(remote_track_id="t1", artist="A", title="B", position=0),)
    return RemotePlaylistSnapshot(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id=remote_id,
        name=name,
        snapshot_at_iso="2026-07-11T10:00:00Z",
        tracks=tracks,
        track_count=1,
        checksum=remote_playlist_snapshot_checksum(tracks),
        source_kind="provider_library",
    )


def _terminal_result(*, phase: ImportPhase = ImportPhase.COMPLETED) -> ImportResultState:
    return ImportResultState(
        playlist_name="Pool Party",
        outcomes=(ImportTrackOutcome("Artist", "Track", "Main", ImportTrackStatus.ADDED),),
        phase=phase,
    )


def _seed_multi_provider_playlist(
    provider: RepositoryProvider,
    *,
    apple_remote: str = "apple-1",
    spotify_remote: str = "spotify-1",
    youtube_remote: str = "youtube-1",
) -> ManagedPlaylistDetail:
    detail = ManagedPlaylistDetail(
        summary=ManagedPlaylistSummary(
            local_playlist_id="hist-sess-multi",
            name="Multi Mix",
            provider_id=ProviderId.APPLE_MUSIC,
            track_count=1,
            sync_status="synced",
            provider_playlist_id=apple_remote,
            linked_remote_refs=(
                LinkedRemoteRef(
                    provider_id=ProviderId.APPLE_MUSIC,
                    remote_playlist_id=apple_remote,
                    snapshot_checksum="apple-cs",
                ),
                LinkedRemoteRef(
                    provider_id=ProviderId.SPOTIFY,
                    remote_playlist_id=spotify_remote,
                    snapshot_checksum="spotify-cs",
                ),
                LinkedRemoteRef(
                    provider_id=ProviderId.YOUTUBE_MUSIC,
                    remote_playlist_id=youtube_remote,
                    snapshot_checksum="youtube-cs",
                ),
            ),
            history_session_id="sess-multi",
        ),
        tracks=(),
    )
    provider.managed_playlist_repository().upsert(detail)
    return detail


def test_app_restart_reads_persisted_repository(tmp_path: Path) -> None:
    """Simulates app relaunch: new RepositoryProvider instance, same JSON files."""
    paths = _provider(tmp_path)
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-restart",
                name="Restart Mix",
                track_count=1,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"remote-restart": _apple_snapshot("remote-restart", "Restart Mix")},
    )
    RegisterGeneratedImport(
        paths.managed_playlist_repository(),
        paths.snapshot_archive(),
    ).execute(
        history_session_id="sess-restart",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Restart Mix",
        import_result=_terminal_result(),
        read_port=read_port,
    )

    relaunched = RepositoryProvider(
        playlists_path=tmp_path / "managed_playlists.json",
        snapshots_dir=tmp_path / "snapshots",
    )
    playlists = relaunched.managed_playlist_repository().list_playlists()
    assert len(playlists) == 1
    assert playlists[0].summary.provider_playlist_id == "remote-restart"


def test_register_upserts_when_repository_already_populated(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    repo = provider.managed_playlist_repository()
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-populated",
                name="Populated",
                track_count=1,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"remote-populated": _apple_snapshot("remote-populated", "Populated")},
    )
    use_case = RegisterGeneratedImport(repo, provider.snapshot_archive())
    use_case.execute(
        history_session_id="sess-populated",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Populated",
        import_result=_terminal_result(phase=ImportPhase.PARTIAL_SUCCESS),
        read_port=read_port,
    )
    use_case.execute(
        history_session_id="sess-populated",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Populated",
        import_result=_terminal_result(phase=ImportPhase.COMPLETED),
        read_port=read_port,
    )
    assert len(repo.list_playlists()) == 1
    loaded = repo.get_playlist("hist-sess-populated")
    assert loaded is not None
    assert loaded.summary.playlist_version == 2


def test_two_successive_retries_increment_version(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-retry2",
                name="Retry Twice",
                track_count=1,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"remote-retry2": _apple_snapshot("remote-retry2", "Retry Twice")},
    )
    use_case = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    )
    for _ in range(3):
        detail = use_case.execute(
            history_session_id="sess-retry2",
            provider_id=ProviderId.APPLE_MUSIC,
            playlist_name="Retry Twice",
            import_result=_terminal_result(),
            read_port=read_port,
        )
    assert detail is not None
    assert detail.summary.playlist_version == 3


def test_playlist_without_remote_id_is_not_linked(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    detail = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    ).execute(
        history_session_id="sess-unlinked",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="No Remote",
        import_result=_terminal_result(),
        read_port=_FakeReadPort(playlists=()),
    )
    assert detail is not None
    assert detail.summary.sync_status == "not_linked"
    assert detail.summary.linked_remote_refs == ()
    assert detail.summary.provider_playlist_id == ""


def test_renamed_provider_playlist_stays_unlinked_without_name_match(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-renamed",
                name="New Name On Provider",
                track_count=1,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"remote-renamed": _apple_snapshot("remote-renamed", "New Name On Provider")},
    )
    detail = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    ).execute(
        history_session_id="sess-renamed",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Old Local Name",
        import_result=_terminal_result(),
        read_port=read_port,
    )
    assert detail is not None
    assert detail.summary.sync_status == "not_linked"


def test_provider_inaccessible_marks_not_linked(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    detail = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    ).execute(
        history_session_id="sess-down",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Down Provider",
        import_result=_terminal_result(),
        read_port=_FakeReadPort(playlists=(), list_error=RuntimeError("provider offline")),
    )
    assert detail is not None
    assert detail.summary.sync_status == "not_linked"


def test_snapshot_read_failure_preserves_link_without_checksum_update(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="remote-snap-fail",
                name="Snapshot Fail",
                track_count=1,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={},
        get_error_for={"remote-snap-fail"},
    )
    detail = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    ).execute(
        history_session_id="sess-snap-fail",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Snapshot Fail",
        import_result=_terminal_result(),
        read_port=read_port,
    )
    assert detail is not None
    assert detail.summary.provider_playlist_id == "remote-snap-fail"
    assert detail.summary.linked_remote_refs[0].snapshot_checksum == ""


def test_apple_retry_preserves_spotify_and_youtube_refs(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    _seed_multi_provider_playlist(provider)
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="apple-updated",
                name="Multi Mix",
                track_count=1,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"apple-updated": _apple_snapshot("apple-updated", "Multi Mix")},
    )
    detail = RegisterGeneratedImport(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    ).execute(
        history_session_id="sess-multi",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Multi Mix",
        import_result=_terminal_result(),
        read_port=read_port,
    )
    assert detail is not None
    refs = {ref.provider_id: ref.remote_playlist_id for ref in detail.summary.linked_remote_refs}
    assert refs[ProviderId.APPLE_MUSIC] == "apple-updated"
    assert refs[ProviderId.SPOTIFY] == "spotify-1"
    assert refs[ProviderId.YOUTUBE_MUSIC] == "youtube-1"


def test_apple_retry_preserves_spotify_only(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    repo = provider.managed_playlist_repository()
    repo.upsert(
        ManagedPlaylistDetail(
            summary=ManagedPlaylistSummary(
                local_playlist_id="hist-sess-dual",
                name="Dual",
                provider_id=ProviderId.APPLE_MUSIC,
                track_count=1,
                sync_status="synced",
                linked_remote_refs=(
                    LinkedRemoteRef(
                        provider_id=ProviderId.APPLE_MUSIC,
                        remote_playlist_id="apple-old",
                        snapshot_checksum="a",
                    ),
                    LinkedRemoteRef(
                        provider_id=ProviderId.SPOTIFY,
                        remote_playlist_id="spotify-keep",
                        snapshot_checksum="s",
                    ),
                ),
                history_session_id="sess-dual",
            ),
            tracks=(),
        )
    )
    read_port = _FakeReadPort(
        playlists=(
            RemotePlaylist(
                provider_id=ProviderId.APPLE_MUSIC,
                remote_playlist_id="apple-new",
                name="Dual",
                track_count=1,
                is_public=False,
                owner_label="Apple Music",
                snapshot_at_iso="2026-07-11T10:00:00Z",
            ),
        ),
        snapshots={"apple-new": _apple_snapshot("apple-new", "Dual")},
    )
    detail = RegisterGeneratedImport(repo, provider.snapshot_archive()).execute(
        history_session_id="sess-dual",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Dual",
        import_result=_terminal_result(),
        read_port=read_port,
    )
    assert detail is not None
    refs = {ref.provider_id: ref.remote_playlist_id for ref in detail.summary.linked_remote_refs}
    assert refs[ProviderId.APPLE_MUSIC] == "apple-new"
    assert refs[ProviderId.SPOTIFY] == "spotify-keep"


def test_failed_apple_link_retry_preserves_existing_apple_ref(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    repo = provider.managed_playlist_repository()
    repo.upsert(
        ManagedPlaylistDetail(
            summary=ManagedPlaylistSummary(
                local_playlist_id="hist-sess-preserve",
                name="Preserve",
                provider_id=ProviderId.APPLE_MUSIC,
                track_count=1,
                sync_status="synced",
                provider_playlist_id="apple-keep",
                linked_remote_refs=(
                    LinkedRemoteRef(
                        provider_id=ProviderId.APPLE_MUSIC,
                        remote_playlist_id="apple-keep",
                        snapshot_checksum="cs",
                    ),
                    LinkedRemoteRef(
                        provider_id=ProviderId.SPOTIFY,
                        remote_playlist_id="spotify-keep",
                        snapshot_checksum="cs2",
                    ),
                ),
                history_session_id="sess-preserve",
            ),
            tracks=(),
        )
    )
    detail = RegisterGeneratedImport(repo, provider.snapshot_archive()).execute(
        history_session_id="sess-preserve",
        provider_id=ProviderId.APPLE_MUSIC,
        playlist_name="Preserve",
        import_result=_terminal_result(),
        read_port=_FakeReadPort(playlists=(), list_error=RuntimeError("offline")),
    )
    assert detail is not None
    refs = {ref.provider_id: ref.remote_playlist_id for ref in detail.summary.linked_remote_refs}
    assert refs[ProviderId.APPLE_MUSIC] == "apple-keep"
    assert refs[ProviderId.SPOTIFY] == "spotify-keep"


def test_managed_local_playlist_id_double_hist_prefix_documented() -> None:
    session_id = "hist-614b1e19-9ab2-4b1d-833c-6158053f5097"
    assert managed_local_playlist_id_from_history(session_id) == f"hist-{session_id}"


def test_merge_linked_remote_refs_unit() -> None:
    existing = ManagedPlaylistDetail(
        summary=ManagedPlaylistSummary(
            local_playlist_id="mpl-1",
            name="X",
            provider_id=ProviderId.APPLE_MUSIC,
            track_count=0,
            sync_status="synced",
            linked_remote_refs=(
                LinkedRemoteRef(
                    provider_id=ProviderId.SPOTIFY,
                    remote_playlist_id="sp-1",
                    snapshot_checksum="s",
                ),
            ),
        ),
        tracks=(),
    )
    merged = merge_linked_remote_refs(
        existing,
        ProviderId.APPLE_MUSIC,
        RemotePlaylistLinkResult(
            status=RemoteLinkStatus.LINKED,
            remote_playlist_id="am-1",
            snapshot_checksum="a",
        ),
        "a",
    )
    providers = {ref.provider_id for ref in merged}
    assert providers == {ProviderId.APPLE_MUSIC, ProviderId.SPOTIFY}
