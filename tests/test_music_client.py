from __future__ import annotations

from unittest.mock import MagicMock, patch

from playlist_builder.core.models import TrackAddResult, TrackAddStatus, TrackRef
from playlist_builder.music.client import MusicClient


def test_add_tracks_preserves_result_order_with_skips():
    tracks = [
        TrackRef(artist="A", title="One", section="S1"),
        TrackRef(artist="B", title="Two", section="S1"),
        TrackRef(artist="C", title="Three", section="S2"),
        TrackRef(artist="D", title="Four", section="S2"),
    ]
    client = MusicClient()
    existing = {tracks[1].key, tracks[3].key}

    with patch.object(
        client,
        "_add_tracks_batch",
        return_value=[
            TrackAddResult(track=tracks[0], status=TrackAddStatus.ADDED),
            TrackAddResult(track=tracks[2], status=TrackAddStatus.NOT_FOUND),
        ],
    ) as batch_mock:
        results = client.add_tracks("Test", tracks, existing_keys=set(existing))

    assert [result.track.title for result in results] == ["One", "Two", "Three", "Four"]
    assert [result.status for result in results] == [
        TrackAddStatus.ADDED,
        TrackAddStatus.SKIPPED,
        TrackAddStatus.NOT_FOUND,
        TrackAddStatus.SKIPPED,
    ]
    batch_mock.assert_called_once()


def test_sync_playlist_order_uses_import_service():
    tracks = [TrackRef(artist="Kygo", title="Firestone")]
    client = MusicClient()

    with patch.object(client._service, "import_playlist", return_value=MagicMock(results=())) as import_mock:
        client.sync_playlist_order("Test", tracks)

    import_mock.assert_called_once()
    assert import_mock.call_args.kwargs.get("sync") is True


def test_normalize_key():
    assert MusicClient._normalize_key("Kygo::Firestone") == "kygo::firestone"
