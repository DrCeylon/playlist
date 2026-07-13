from __future__ import annotations

from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.integration.youtube_music.auth import YouTubeMusicAuthPort
from playlist_builder.integration.youtube_music.client import build_youtube_music_client, wrap_client_error
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistTrack


class YouTubeMusicPlaylistWritePort(ProviderPlaylistWritePort):
    """Write user playlists on YouTube Music via ytmusicapi."""

    def __init__(self, auth: YouTubeMusicAuthPort) -> None:
        self._auth = auth

    def _client(self):
        client = build_youtube_music_client(self._auth.headers_path())
        if client is None:
            raise ValueError(self._auth.unavailable_reason() or "Connexion YouTube Music requise.")
        return client

    def create_playlist(self, name: str) -> str:
        playlist_name = name.strip()
        if not playlist_name:
            raise ValueError("Le nom de playlist est requis.")
        client = self._client()
        try:
            for item in client.list_library_playlists():
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title", "")).strip()
                playlist_id = str(item.get("playlistId") or "").strip()
                if title == playlist_name and playlist_id:
                    return playlist_id
            return client.create_playlist(playlist_name)
        except Exception as exc:
            raise wrap_client_error(exc) from exc

    def upsert_tracks(self, remote_playlist_id: str, tracks: tuple[RemotePlaylistTrack, ...]) -> None:
        video_ids = [track.remote_track_id.strip() for track in tracks if track.remote_track_id.strip()]
        if not video_ids:
            return
        client = self._client()
        try:
            client.add_playlist_items(remote_playlist_id, video_ids)
        except Exception as exc:
            raise wrap_client_error(exc) from exc

    def remove_tracks(self, remote_playlist_id: str, remote_track_ids: tuple[str, ...]) -> None:
        ids = [item.strip() for item in remote_track_ids if item.strip()]
        if not ids:
            return
        client = self._client()
        try:
            client.remove_playlist_items(remote_playlist_id, ids)
        except Exception as exc:
            raise wrap_client_error(exc) from exc
