from __future__ import annotations

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.integration.youtube_music.auth import YouTubeMusicAuthPort
from playlist_builder.integration.youtube_music.client import YouTubeMusicClient, build_youtube_music_client, wrap_client_error
from playlist_builder.integration.youtube_music.mapper import map_library_playlist, map_playlist_snapshot
from playlist_builder.integration.youtube_music.playlist_id import normalize_remote_playlist_id
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylist, RemotePlaylistSnapshot, utc_now_iso


class YouTubeMusicPlaylistReadPort(ProviderPlaylistReadPort):
    """Best-effort playlist reads for YouTube Music (library + public playlists)."""

    def __init__(self, auth: YouTubeMusicAuthPort) -> None:
        self._auth = auth

    def _client(self, *, require_auth: bool = False) -> YouTubeMusicClient | None:
        headers_path = self._auth.headers_path()
        if require_auth and headers_path is None:
            raise ValueError("Connexion YouTube Music requise pour parcourir votre bibliothèque.")
        return build_youtube_music_client(headers_path)

    def list_playlists(self, *, account_id: str | None = None) -> tuple[RemotePlaylist, ...]:
        del account_id
        client = self._client(require_auth=True)
        if client is None:
            raise ValueError(self._auth.unavailable_reason() or "YouTube Music expérimental indisponible.")
        snapshot_at = utc_now_iso()
        try:
            raw_playlists = client.list_library_playlists()
        except Exception as exc:
            raise wrap_client_error(exc) from exc
        return tuple(map_library_playlist(item, snapshot_at_iso=snapshot_at) for item in raw_playlists if isinstance(item, dict))

    def get_playlist(self, remote_playlist_id: str) -> RemotePlaylistSnapshot:
        playlist_id = normalize_remote_playlist_id(remote_playlist_id)
        client = self._client(require_auth=False)
        if client is None:
            raise ValueError(self._auth.unavailable_reason() or "YouTube Music expérimental indisponible.")
        try:
            payload = client.get_playlist(playlist_id)
        except Exception as exc:
            raise wrap_client_error(exc) from exc
        if not isinstance(payload, dict):
            raise ValueError("Réponse playlist YouTube Music invalide.")
        source_kind = "provider_library" if self._auth.auth_state().value == "connected" else "public_catalog"
        source_url = remote_playlist_id if remote_playlist_id.startswith("http") else ""
        return map_playlist_snapshot(
            payload,
            remote_playlist_id=playlist_id,
            source_kind=source_kind,
            source_url=source_url,
        )
