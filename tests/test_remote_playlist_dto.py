from __future__ import annotations

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.ui.shared.dto.remote_playlist import (
    ProviderAuthState,
    RemotePlaylist,
    RemotePlaylistSnapshot,
    RemotePlaylistTrack,
    RemoteProviderAccount,
    remote_playlist_snapshot_checksum,
)


def test_remote_playlist_track_to_dict_is_bridge_safe() -> None:
    track = RemotePlaylistTrack(
        remote_track_id="trk-1",
        artist="Kygo",
        title="Firestone",
        album="Cloud Nine",
        duration_ms=245_000,
        position=1,
        provider_metadata={"genre": "edm"},
    )
    payload = track.to_dict()
    assert payload["remote_track_id"] == "trk-1"
    assert payload["artist"] == "Kygo"
    assert payload["provider_metadata"] == {"genre": "edm"}
    assert "persistent_id" not in payload


def test_remote_playlist_to_dict_serializes_provider_id() -> None:
    playlist = RemotePlaylist(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id="pl-42",
        name="Road Trip",
        track_count=12,
        is_public=False,
        owner_label="me",
        snapshot_at_iso="2026-07-09T12:00:00Z",
    )
    payload = playlist.to_dict()
    assert payload["provider_id"] == "apple_music"
    assert payload["remote_playlist_id"] == "pl-42"
    assert payload["track_count"] == 12


def test_remote_playlist_snapshot_round_trip_and_checksum() -> None:
    tracks = (
        RemotePlaylistTrack(
            remote_track_id="a",
            artist="Artist A",
            title="Song A",
            position=1,
        ),
        RemotePlaylistTrack(
            remote_track_id="b",
            artist="Artist B",
            title="Song B",
            position=2,
        ),
    )
    checksum = remote_playlist_snapshot_checksum(tracks)
    snapshot = RemotePlaylistSnapshot(
        provider_id=ProviderId.SPOTIFY,
        remote_playlist_id="spotify-pl-1",
        name="Discover Weekly",
        snapshot_at_iso="2026-07-09T12:00:00Z",
        tracks=tracks,
        track_count=len(tracks),
        checksum=checksum,
        source_kind="provider_library",
    )
    payload = snapshot.to_dict()
    assert payload["provider_id"] == "spotify"
    assert len(payload["tracks"]) == 2
    assert payload["checksum"] == checksum
    assert payload["tracks"][0]["position"] == 1


def test_remote_provider_account_never_includes_secrets() -> None:
    account = RemoteProviderAccount(
        provider_id=ProviderId.YOUTUBE_MUSIC,
        display_name="YouTube (masked)",
        auth_state=ProviderAuthState.EXPERIMENTAL_UNAVAILABLE,
        last_connected_at_iso="",
        capabilities=frozenset({ProviderCapability.EXPERIMENTAL}),
    )
    payload = account.to_dict()
    assert payload["auth_state"] == "experimental_unavailable"
    assert "token" not in payload
    assert "cookie" not in payload
    assert payload["capabilities"] == ["experimental"]
