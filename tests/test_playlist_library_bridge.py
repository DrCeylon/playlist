from __future__ import annotations

from pathlib import Path

from playlist_builder.app.bridge_runtime.playlist_library import (
    get_managed_playlist,
    import_remote_playlist,
    list_managed_playlists,
)
from playlist_builder.app.playlist_library.migration import HistoryToRepositoryMigration
from playlist_builder.app.playlist_library.provider import RepositoryProvider
from playlist_builder.ui.bridge import BridgeCommand, JsonRpcEngineBridge
from playlist_builder.ui.bridge.protocol import EngineBridgeBackend


class _RepositoryPlaylistBackend:
    def __init__(self, tmp_path: Path) -> None:
        self._provider = RepositoryProvider(
            playlists_path=tmp_path / "managed_playlists.json",
            snapshots_dir=tmp_path / "snapshots",
        )
        self._migration = HistoryToRepositoryMigration(
            self._provider.managed_playlist_repository(),
        )

    def list_history(self) -> tuple[dict[str, object], ...]:
        return (
            {
                "session_id": "sess-1",
                "playlist_name": "Demo Playlist",
                "provider_id": "apple_music",
                "status": "imported",
                "track_count": 1,
                "finished_at_iso": "2026-07-08T10:00:00",
                "started_at_iso": "2026-07-08T09:00:00",
                "import_result": {
                    "outcomes": [
                        {"artist": "Daft Punk", "title": "One More Time", "section": "Main", "status": "added"},
                    ],
                },
            },
        )

    def list_managed_playlists(self) -> tuple[dict[str, object], ...]:
        return list_managed_playlists(self._provider, self._migration, self.list_history())

    def get_managed_playlist(self, local_playlist_id: str) -> dict[str, object] | None:
        return get_managed_playlist(
            self._provider,
            self._migration,
            self.list_history(),
            local_playlist_id,
        )

    def import_remote_playlist(self, params: dict[str, object]) -> dict[str, object]:
        return import_remote_playlist(self._provider, params)


def test_list_managed_playlists_migrates_from_history(tmp_path: Path) -> None:
    backend = _RepositoryPlaylistBackend(tmp_path)
    playlists = backend.list_managed_playlists()
    assert len(playlists) == 1
    assert playlists[0]["local_playlist_id"] == "hist-sess-1"
    assert playlists[0]["origin"] == "generated"
    assert playlists[0]["playlist_version"] == 1


def test_get_managed_playlist_includes_migrated_tracks(tmp_path: Path) -> None:
    backend = _RepositoryPlaylistBackend(tmp_path)
    detail = backend.get_managed_playlist("hist-sess-1")
    assert detail is not None
    playlist = detail["playlist"]
    assert isinstance(playlist, dict)
    tracks = playlist.get("tracks", [])
    assert len(tracks) == 1
    assert tracks[0]["artist"] == "Daft Punk"


def test_json_rpc_import_remote_playlist_command(tmp_path: Path) -> None:
    backend = _RepositoryPlaylistBackend(tmp_path)
    bridge = JsonRpcEngineBridge(backend=backend)  # type: ignore[arg-type]
    messages = bridge.handle(
        {
            "id": "import-1",
            "command": BridgeCommand.IMPORT_REMOTE_PLAYLIST.value,
            "params": {
                "remote_playlist": {
                    "provider_id": "apple_music",
                    "remote_playlist_id": "p.remote.1",
                    "name": "Remote Import",
                    "snapshot_at_iso": "2026-07-10T12:00:00",
                    "track_count": 1,
                    "checksum": "deadbeefcafebabe",
                    "source_kind": "provider_library",
                    "tracks": [
                        {
                            "remote_track_id": "t1",
                            "artist": "Artist",
                            "title": "Title",
                            "position": 0,
                        },
                    ],
                },
            },
        }
    )
    assert messages[-1]["ok"] is True
    playlist = messages[-1]["result"]["playlist"]
    assert playlist["name"] == "Remote Import"
    assert playlist["origin"] == "provider_library"
    assert len(playlist["linked_remote_refs"]) == 1
    assert playlist["linked_remote_refs"][0]["snapshot_checksum"] == "deadbeefcafebabe"


def test_json_rpc_list_managed_playlists_command(tmp_path: Path) -> None:
    bridge = JsonRpcEngineBridge(backend=_RepositoryPlaylistBackend(tmp_path))  # type: ignore[arg-type]
    messages = bridge.handle(
        {"id": "pl-1", "command": BridgeCommand.LIST_MANAGED_PLAYLISTS.value, "params": {}}
    )
    assert messages[-1]["ok"] is True
    playlists = messages[-1]["result"]["playlists"]
    assert len(playlists) == 1
    assert playlists[0]["name"] == "Demo Playlist"
