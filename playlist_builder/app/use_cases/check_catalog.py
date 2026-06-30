from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.app.factory import AppContext
from playlist_builder.canonical.models import CanonicalSearchRequest
from playlist_builder.core.models import CatalogMatch, PlaylistDefinition, TrackRef


@dataclass(frozen=True, slots=True)
class CheckCatalogResult:
    playlist_name: str
    matches: tuple[CatalogMatch, ...]


class CheckCatalogUseCase:
    """Check playlist tracks against a provider catalog via the integration gateway."""

    def __init__(self, context: AppContext) -> None:
        self._context = context

    def execute(self, playlist: PlaylistDefinition) -> CheckCatalogResult:
        matches: list[CatalogMatch] = []
        for track in playlist.tracks:
            matches.append(self._search_track(track))
        return CheckCatalogResult(playlist_name=playlist.name, matches=tuple(matches))

    def _search_track(self, track: TrackRef) -> CatalogMatch:
        response = self._context.gateway.search_catalog(
            CanonicalSearchRequest(
                query=f"{track.artist} {track.title}".strip(),
                wanted_artist=track.artist,
                wanted_title=track.title,
            )
        )
        if not response.candidates:
            return CatalogMatch(query=track, error="Aucune correspondance catalogue.")
        candidate = response.candidates[0]
        url = candidate.provider_hints[0] if candidate.provider_hints else ""
        return CatalogMatch(
            query=track,
            matched_artist=candidate.track.artist.name,
            matched_title=candidate.track.title,
            url=url,
            raw={"confidence": candidate.raw_confidence},
        )
