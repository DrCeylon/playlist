from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from playlist_builder.canonical.contracts import CatalogSearchPort
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalCandidate, CanonicalSearchRequest, CanonicalTrack
from playlist_builder.integration.youtube_music.auth import YouTubeMusicAuthPort
from playlist_builder.integration.youtube_music.client import build_youtube_music_client, wrap_client_error


class YouTubeMusicResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class YouTubeMusicResolutionOutcome:
    track: CanonicalTrack
    status: YouTubeMusicResolutionStatus
    video_id: str = ""
    error: str = ""


class YouTubeMusicResolver:
    """Resolve playlist tracks to YouTube Music video IDs via catalog search."""

    def __init__(self, auth: YouTubeMusicAuthPort, *, catalog: CatalogSearchPort | None = None) -> None:
        self._auth = auth
        self._catalog = catalog

    def _client(self):
        client = build_youtube_music_client(self._auth.headers_path())
        if client is None:
            raise ValueError(self._auth.unavailable_reason() or "YouTube Music indisponible.")
        return client

    def resolve_batch(self, rows: list[tuple[CanonicalTrack, str]]) -> list[YouTubeMusicResolutionOutcome]:
        return [self.resolve(track, section=section) for track, section in rows]

    def resolve(self, track: CanonicalTrack, *, section: str = "Playlist") -> YouTubeMusicResolutionOutcome:
        del section
        query = f"{track.artist.display_name} {track.title}".strip()
        if not query:
            return YouTubeMusicResolutionOutcome(
                track=track,
                status=YouTubeMusicResolutionStatus.ERROR,
                error="Artiste ou titre manquant.",
            )
        try:
            if self._catalog is not None:
                response = self._catalog.search(CanonicalSearchRequest(query=query, limit=5))
                for candidate in response.candidates:
                    video_id = str(candidate.provider_track_id or "").strip()
                    if video_id:
                        return YouTubeMusicResolutionOutcome(
                            track=track,
                            status=YouTubeMusicResolutionStatus.RESOLVED,
                            video_id=video_id,
                        )
            client = self._client()
            results = client.search_songs(query, limit=5)
            for item in results:
                if not isinstance(item, dict):
                    continue
                video_id = str(item.get("videoId") or "").strip()
                if video_id:
                    return YouTubeMusicResolutionOutcome(
                        track=track,
                        status=YouTubeMusicResolutionStatus.RESOLVED,
                        video_id=video_id,
                    )
        except Exception as exc:
            return YouTubeMusicResolutionOutcome(
                track=track,
                status=YouTubeMusicResolutionStatus.ERROR,
                error=str(wrap_client_error(exc)),
            )
        return YouTubeMusicResolutionOutcome(
            track=track,
            status=YouTubeMusicResolutionStatus.NOT_FOUND,
            error="Introuvable sur YouTube Music",
        )

    def probe_library_presence(self, track: CanonicalTrack, *, section: str = "Playlist") -> bool:
        del track, section
        return False

    def probe_library_presence_detail(
        self,
        track: CanonicalTrack,
        *,
        section: str = "Playlist",
    ) -> tuple[bool, str | None]:
        del track, section
        return False, "L'ajout manuel n'est pas requis pour YouTube Music."
