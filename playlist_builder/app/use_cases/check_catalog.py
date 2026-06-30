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
    """Check playlist tracks against the Apple Music catalog gateway."""

    def __init__(self, context: AppContext) -> None:
        self._context = context

    def execute(self, playlist: PlaylistDefinition) -> CheckCatalogResult:
        catalog = self._context.apple_music.catalog
        matches: list[CatalogMatch] = []
        for track in playlist.tracks:
            matches.append(self._search_track(track, catalog))
        return CheckCatalogResult(playlist_name=playlist.name, matches=tuple(matches))

    @staticmethod
    def _search_track(track: TrackRef, catalog) -> CatalogMatch:
        response = catalog.search(
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
