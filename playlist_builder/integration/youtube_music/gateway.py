from __future__ import annotations

from pathlib import Path

from playlist_builder.canonical.contracts import CatalogSearchPort, ProviderGateway
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.integration.ports.provider_auth import ProviderAuthPort
from playlist_builder.integration.youtube_music.auth import YouTubeMusicAuthPort
from playlist_builder.integration.youtube_music.catalog import YouTubeMusicCatalogGateway
from playlist_builder.integration.youtube_music.experimental_guard import experimental_unavailable_reason, is_ytmusicapi_installed
from playlist_builder.integration.youtube_music.read_port import YouTubeMusicPlaylistReadPort


class YouTubeMusicProviderGateway(ProviderGateway):
    """Experimental YouTube Music gateway — optional dependency, no write port in 6.6."""

    def __init__(self, auth: YouTubeMusicAuthPort) -> None:
        self._auth = auth
        self._read_port = YouTubeMusicPlaylistReadPort(auth)
        self._catalog = YouTubeMusicCatalogGateway(auth)

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.YOUTUBE_MUSIC

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        caps = {
            ProviderCapability.EXPERIMENTAL,
            ProviderCapability.AUTHENTICATION,
        }
        if is_ytmusicapi_installed():
            caps.update(
                {
                    ProviderCapability.PUBLIC_PLAYLIST_IMPORT,
                    ProviderCapability.CATALOG_SEARCH,
                }
            )
            if self._auth.auth_state().value == "connected":
                caps.add(ProviderCapability.PLAYLIST_LIBRARY_BROWSE)
        return frozenset(caps)

    @property
    def catalog(self) -> CatalogSearchPort | None:
        if not is_ytmusicapi_installed():
            return None
        return self._catalog

    @property
    def library(self):
        return None

    @property
    def delivery(self):
        return None

    @property
    def playlist_read(self) -> ProviderPlaylistReadPort | None:
        if not is_ytmusicapi_installed():
            return None
        return self._read_port

    @property
    def playlist_write(self) -> ProviderPlaylistWritePort | None:
        return None

    @property
    def auth(self) -> ProviderAuthPort:
        return self._auth

    def unavailable_reason(self) -> str:
        return experimental_unavailable_reason()


def build_youtube_music_gateway(*, auth_config_path: Path) -> YouTubeMusicProviderGateway:
    return YouTubeMusicProviderGateway(YouTubeMusicAuthPort(auth_config_path))
