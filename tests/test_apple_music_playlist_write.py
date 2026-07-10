from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from playlist_builder.integration.apple_music.playlist_write_port import AppleMusicPlaylistWritePort
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistTrack


def test_apple_write_port_upsert_skips_existing_keys() -> None:
    script = MagicMock()
    script.playlist_name_for_id.return_value = "My Playlist"
    script.load_playlist_keys.return_value = {"daft punk::one more time"}
    script.collect_candidates_batch.return_value = [[AppleMusicTrack("pid-1", "Daft Punk", "One More Time", "q")]]
    script.add_tracks_by_persistent_id_batch.return_value = ["added"]
    port = AppleMusicPlaylistWritePort(script)
    port.upsert_tracks(
        "playlist-id-1",
        (
            RemotePlaylistTrack(
                remote_track_id="",
                artist="Daft Punk",
                title="One More Time",
                position=1,
            ),
        ),
    )
    script.add_tracks_by_persistent_id_batch.assert_not_called()


def test_apple_write_port_upsert_raises_when_track_missing() -> None:
    script = MagicMock()
    script.playlist_name_for_id.return_value = "My Playlist"
    script.load_playlist_keys.return_value = set()
    script.collect_candidates_batch.return_value = [[]]
    port = AppleMusicPlaylistWritePort(script)
    with pytest.raises(ValueError, match="introuvable"):
        port.upsert_tracks(
            "playlist-id-1",
            (RemotePlaylistTrack(remote_track_id="", artist="X", title="Y", position=1),),
        )
