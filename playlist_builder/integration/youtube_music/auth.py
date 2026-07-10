from __future__ import annotations

from pathlib import Path

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.integration.ports.provider_auth import ProviderAuthPort
from playlist_builder.integration.youtube_music.client import build_youtube_music_client, load_headers_file
from playlist_builder.integration.youtube_music.experimental_guard import experimental_unavailable_reason, is_ytmusicapi_installed
from playlist_builder.integration.youtube_music.mapper import YouTubeMusicAuthConfigStore
from playlist_builder.integration.youtube_music.secrets import sanitize_user_message
from playlist_builder.ui.shared.dto.remote_playlist import ProviderAuthState


class YouTubeMusicAuthPort(ProviderAuthPort):
    """Experimental auth boundary — stores a local headers file path only."""

    def __init__(self, config_path: Path) -> None:
        self._store = YouTubeMusicAuthConfigStore(config_path)

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.YOUTUBE_MUSIC

    def auth_state(self) -> ProviderAuthState:
        if not is_ytmusicapi_installed():
            return ProviderAuthState.EXPERIMENTAL_UNAVAILABLE
        headers_path = self._store.headers_path()
        if headers_path is None:
            return ProviderAuthState.DISCONNECTED
        if not headers_path.exists():
            return ProviderAuthState.EXPIRED
        return ProviderAuthState.CONNECTED

    def connect(self, *, params: dict[str, str]) -> ProviderAuthState:
        if not is_ytmusicapi_installed():
            return ProviderAuthState.EXPERIMENTAL_UNAVAILABLE

        headers_path_raw = str(params.get("headers_file_path", "")).strip()
        if not headers_path_raw:
            raise ValueError("headers_file_path est requis pour connecter YouTube Music.")

        headers_path = Path(headers_path_raw).expanduser()
        load_headers_file(headers_path)

        display_name = str(params.get("display_name", "")).strip() or "YouTube Music"
        client = build_youtube_music_client(headers_path)
        if client is None:
            return ProviderAuthState.EXPERIMENTAL_UNAVAILABLE

        try:
            client.list_library_playlists()
        except Exception as exc:
            raise ValueError(sanitize_user_message(f"Authentification YouTube Music refusée : {exc}")) from exc

        self._store.save(
            {
                "headers_file_path": str(headers_path),
                "display_name": display_name,
            }
        )
        return ProviderAuthState.CONNECTED

    def disconnect(self) -> ProviderAuthState:
        self._store.clear()
        return ProviderAuthState.DISCONNECTED

    def account_display_name(self) -> str:
        return self._store.load().get("display_name", "")

    def headers_path(self) -> Path | None:
        return self._store.headers_path()

    def unavailable_reason(self) -> str:
        return experimental_unavailable_reason()
