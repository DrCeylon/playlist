from __future__ import annotations

from playlist_builder.canonical.contracts import CatalogSearchPort
from playlist_builder.integration.youtube_music.auth import YouTubeMusicAuthPort
from playlist_builder.integration.youtube_music.delivery import YouTubeMusicDelivery
from playlist_builder.integration.youtube_music.resolver import YouTubeMusicResolver


class YouTubeMusicImportService:
    """Orchestrates YouTube Music catalog resolution and playlist delivery."""

    def __init__(self, auth: YouTubeMusicAuthPort, *, catalog: CatalogSearchPort | None = None) -> None:
        self._auth = auth
        self._resolver = YouTubeMusicResolver(auth, catalog=catalog)
        self._delivery = YouTubeMusicDelivery(auth)

    @property
    def resolver(self) -> YouTubeMusicResolver:
        return self._resolver

    @property
    def delivery(self) -> YouTubeMusicDelivery:
        return self._delivery
