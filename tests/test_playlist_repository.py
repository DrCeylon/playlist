from __future__ import annotations

from pathlib import Path

import pytest

from playlist_builder.app.playlist_library.import_remote import ImportRemotePlaylist
from playlist_builder.app.playlist_library.json_repository import JsonManagedPlaylistRepository
from playlist_builder.app.playlist_library.migration import HistoryToRepositoryMigration
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.app.playlist_library.snapshot_archive import SnapshotArchive, snapshot_id_from_checksum
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_library import PlaylistOrigin
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack


@pytest.fixture
def repo_paths(tmp_path: Path) -> tuple[Path, Path]:
    return tmp_path / "managed_playlists.json", tmp_path / "snapshots"


def _sample_snapshot() -> RemotePlaylistSnapshot:
    tracks = (
        RemotePlaylistTrack(
            remote_track_id="am-1",
            artist="Artist A",
            title="Song One",
            position=0,
        ),
        RemotePlaylistTrack(
            remote_track_id="am-2",
            artist="Artist B",
            title="Song Two",
            position=1,
        ),
    )
    return RemotePlaylistSnapshot(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id="remote-pl-1",
        name="Imported Playlist",
        snapshot_at_iso="2026-07-10T10:00:00",
        tracks=tracks,
        track_count=len(tracks),
        checksum="abc123checksum01",
        source_kind="provider_library",
    )


def test_json_repository_crud(repo_paths: tuple[Path, Path]) -> None:
    playlists_path, _ = repo_paths
    repository = JsonManagedPlaylistRepository(playlists_path)
    assert repository.list_playlists() == []

    use_case = ImportRemotePlaylist(repository, SnapshotArchive(repo_paths[1]))
    detail = use_case.execute(_sample_snapshot(), local_playlist_id="mpl-test-1")
    assert detail.summary.local_playlist_id == "mpl-test-1"
    assert detail.summary.playlist_version == 1
    assert detail.summary.origin == PlaylistOrigin.PROVIDER_LIBRARY.value
    assert len(detail.tracks) == 2

    loaded = repository.get_playlist("mpl-test-1")
    assert loaded is not None
    assert loaded.summary.name == "Imported Playlist"
    assert repository.delete("mpl-test-1") is True
    assert repository.get_playlist("mpl-test-1") is None


def test_snapshot_archive_deduplicates_by_checksum(repo_paths: tuple[Path, Path]) -> None:
    _, snapshots_dir = repo_paths
    archive = SnapshotArchive(snapshots_dir)
    snapshot = _sample_snapshot()
    checksum_a = archive.store(snapshot)
    checksum_b = archive.store(snapshot)
    assert checksum_a == checksum_b == snapshot.checksum
    assert snapshot_id_from_checksum(checksum_a) == f"snap-{checksum_a}"
    assert len(list(snapshots_dir.glob("*.json"))) == 1
    loaded = archive.get(checksum_a)
    assert loaded is not None
    assert loaded.name == snapshot.name
    assert len(loaded.tracks) == 2


def test_import_remote_playlist_is_pure_no_gateway(repo_paths: tuple[Path, Path]) -> None:
    provider = RepositoryProvider(playlists_path=repo_paths[0], snapshots_dir=repo_paths[1])
    use_case = ImportRemotePlaylist(
        provider.managed_playlist_repository(),
        provider.snapshot_archive(),
    )
    detail = use_case.execute(_sample_snapshot())
    assert detail.summary.local_playlist_id.startswith("mpl-")
    assert len(detail.summary.linked_remote_refs) == 1
    ref = detail.summary.linked_remote_refs[0]
    assert ref.provider_id == ProviderId.APPLE_MUSIC
    assert ref.remote_playlist_id == "remote-pl-1"
    assert ref.snapshot_checksum == "abc123checksum01"
    assert ref.sync_state == ""
    assert ref.last_sync_at == ""


def test_history_migration_is_idempotent(repo_paths: tuple[Path, Path]) -> None:
    repository = JsonManagedPlaylistRepository(repo_paths[0])
    migration = HistoryToRepositoryMigration(repository)
    sessions = (
        {
            "session_id": "sess-abc",
            "playlist_name": "Rock Mix",
            "provider_id": "apple_music",
            "status": "imported",
            "track_count": 2,
            "started_at_iso": "2026-07-01T10:00:00",
            "finished_at_iso": "2026-07-01T10:05:00",
            "import_result": {
                "outcomes": [
                    {"artist": "A", "title": "One", "section": "Main", "status": "added"},
                    {"artist": "B", "title": "Two", "section": "Main", "status": "not_found"},
                ],
            },
        },
    )
    migration.ensure_migrated(sessions)
    migration.ensure_migrated(sessions)
    playlists = repository.list_playlists()
    assert len(playlists) == 1
    detail = playlists[0]
    assert detail.summary.local_playlist_id == "hist-sess-abc"
    assert detail.summary.origin == PlaylistOrigin.GENERATED.value
    assert len(detail.tracks) == 2
    assert detail.tracks[0].mapping_status == "matched"
    assert detail.tracks[1].mapping_status == "missing_on_provider"


def test_history_migration_picks_up_new_sessions_on_later_call(repo_paths: tuple[Path, Path]) -> None:
    repository = JsonManagedPlaylistRepository(repo_paths[0])
    migration = HistoryToRepositoryMigration(repository)
    first_batch = (
        {
            "session_id": "sess-1",
            "playlist_name": "First",
            "provider_id": "apple_music",
            "status": "imported",
            "track_count": 1,
            "started_at_iso": "2026-07-01T10:00:00",
        },
    )
    migration.ensure_migrated(first_batch)
    second_batch = (
        *first_batch,
        {
            "session_id": "sess-2",
            "playlist_name": "Second",
            "provider_id": "apple_music",
            "status": "imported",
            "track_count": 1,
            "started_at_iso": "2026-07-02T10:00:00",
        },
    )
    migration.ensure_migrated(second_batch)
    playlists = repository.list_playlists()
    assert len(playlists) == 2
    ids = {item.summary.local_playlist_id for item in playlists}
    assert ids == {"hist-sess-1", "hist-sess-2"}


def test_repository_provider_returns_same_instance(repo_paths: tuple[Path, Path]) -> None:
    provider = RepositoryProvider(playlists_path=repo_paths[0], snapshots_dir=repo_paths[1])
    repo_a = provider.managed_playlist_repository()
    repo_b = provider.managed_playlist_repository()
    archive_a = provider.snapshot_archive()
    archive_b = provider.snapshot_archive()
    assert repo_a is repo_b
    assert archive_a is archive_b


def test_json_repository_rejects_newer_schema_version(repo_paths: tuple[Path, Path]) -> None:
    import json

    from playlist_builder.app.playlist_library.errors import UnsupportedSchemaVersionError
    from playlist_builder.app.playlist_library.serialization import SCHEMA_VERSION

    playlists_path, _ = repo_paths
    playlists_path.parent.mkdir(parents=True, exist_ok=True)
    playlists_path.write_text(
        json.dumps({"schema_version": SCHEMA_VERSION + 1, "playlists": []}),
        encoding="utf-8",
    )
    repository = JsonManagedPlaylistRepository(playlists_path)
    with pytest.raises(UnsupportedSchemaVersionError):
        repository.list_playlists()

