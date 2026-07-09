from __future__ import annotations

from playlist_builder.app.bridge_runtime.playlist_library import (
    list_managed_playlists_from_history,
    managed_playlist_detail,
    sync_managed_playlist_stub,
)
from playlist_builder.ui.bridge import BridgeCommand, JsonRpcEngineBridge
from playlist_builder.ui.bridge.protocol import EngineBridgeBackend


class _PlaylistLibraryBackend:
    def list_history(self) -> tuple[dict[str, object], ...]:
        return (
            {
                "session_id": "sess-1",
                "playlist_name": "Demo Playlist",
                "provider_id": "apple_music",
                "status": "imported",
                "track_count": 12,
                "finished_at_iso": "2026-07-08T10:00:00",
            },
        )

    def list_managed_playlists(self) -> tuple[dict[str, object], ...]:
        return list_managed_playlists_from_history(self.list_history())

    def get_managed_playlist(self, local_playlist_id: str) -> dict[str, object] | None:
        return managed_playlist_detail(self, local_playlist_id)

    def sync_managed_playlist(self, params: dict[str, object]) -> dict[str, object]:
        return sync_managed_playlist_stub(params)


def test_list_managed_playlists_from_history_maps_sessions() -> None:
    playlists = list_managed_playlists_from_history(
        (
            {
                "session_id": "abc",
                "playlist_name": "Rock",
                "provider_id": "youtube_music",
                "status": "partial_success",
                "track_count": 8,
            },
        )
    )
    assert len(playlists) == 1
    assert playlists[0]["local_playlist_id"] == "hist-abc"
    assert playlists[0]["provider_id"] == "youtube_music"
    assert playlists[0]["sync_status"] == "partial"


def test_json_rpc_list_managed_playlists_command() -> None:
    bridge = JsonRpcEngineBridge(backend=_PlaylistLibraryBackend())  # type: ignore[arg-type]
    messages = bridge.handle(
        {"id": "pl-1", "command": BridgeCommand.LIST_MANAGED_PLAYLISTS.value, "params": {}}
    )
    assert messages[-1]["ok"] is True
    playlists = messages[-1]["result"]["playlists"]
    assert len(playlists) == 1
    assert playlists[0]["name"] == "Demo Playlist"


def test_json_rpc_sync_managed_playlist_stub() -> None:
    bridge = JsonRpcEngineBridge(backend=_PlaylistLibraryBackend())  # type: ignore[arg-type]
    messages = bridge.handle(
        {
            "id": "sync-1",
            "command": BridgeCommand.SYNC_MANAGED_PLAYLIST.value,
            "params": {
                "local_playlist_id": "hist-sess-1",
                "provider_id": "youtube_music",
                "direction": "pull_from_provider",
            },
        }
    )
    assert messages[-1]["ok"] is True
    sync = messages[-1]["result"]["sync"]
    assert sync["sync_status"] == "pending"
    assert "youtube_music" in sync["message"]
