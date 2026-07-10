from __future__ import annotations

from playlist_builder.canonical.contracts import CatalogSearchPort
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalCandidate, CanonicalSearchRequest, CanonicalSearchResponse, CanonicalTrack
from playlist_builder.integration.youtube_music.auth import YouTubeMusicAuthPort
from playlist_builder.integration.youtube_music.client import build_youtube_music_client, wrap_client_error
from playlist_builder.integration.youtube_music.mapper import _artist_name


class YouTubeMusicCatalogGateway(CatalogSearchPort):
    """Experimental catalog search via ytmusicapi when installed."""

    def __init__(self, auth: YouTubeMusicAuthPort) -> None:
        self._auth = auth

    def search(self, request: CanonicalSearchRequest) -> CanonicalSearchResponse:
        client = build_youtube_music_client(self._auth.headers_path())
        if client is None:
            raise ValueError(self._auth.unavailable_reason() or "YouTube Music expérimental indisponible.")
        query = request.query.strip()
        if not query:
            return CanonicalSearchResponse(request=request, candidates=())
        try:
            results = client.search_songs(query, limit=max(1, min(request.limit, 25)))
        except Exception as exc:
            raise wrap_client_error(exc) from exc

        candidates: list[CanonicalCandidate] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            video_id = str(item.get("videoId") or "").strip()
            artist = _artist_name(item.get("artists"))
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            candidates.append(
                CanonicalCandidate(
                    provider_id=ProviderId.YOUTUBE_MUSIC,
                    provider_track_id=video_id,
                    track=CanonicalTrack(artist=artist, title=title),
                    confidence_score=55.0,
                    source_label="youtube_music_search",
                )
            )
        return CanonicalSearchResponse(request=request, candidates=tuple(candidates))
