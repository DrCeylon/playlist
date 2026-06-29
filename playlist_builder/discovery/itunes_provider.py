from __future__ import annotations

from playlist_builder.catalog.apple_search import AppleCatalogSearch
from playlist_builder.core.models import TrackRef
from playlist_builder.discovery.models import DiscoveryQuery
from playlist_builder.discovery.probe import wanted_match_fields
from playlist_builder.discovery.providers import CandidateProvider
from playlist_builder.planning.models import CandidateTrack, PlaylistRequest


def candidate_from_itunes_match(
    match,
    *,
    query: DiscoveryQuery,
    source: str = "itunes",
) -> CandidateTrack:
    raw = match.raw or {}
    artist = match.matched_artist or query.term
    title = match.matched_title or query.term
    return CandidateTrack(
        track=TrackRef(artist=artist, title=title, section="Discovery"),
        score=max(1.0, 40.0 * query.weight),
        source=source,
        reasons=(f"query:{query.source}:{query.term}",),
        album=str(raw.get("collectionName", "")),
        genre=str(raw.get("primaryGenreName", "")),
        explicit=raw.get("trackExplicitness", "") == "explicit",
    )


class ITunesCandidateProvider(CandidateProvider):
    """Candidate provider backed by the public iTunes Search catalog."""

    name = "itunes"

    def __init__(self, search: AppleCatalogSearch, per_query_limit: int = 10) -> None:
        self.search = search
        self.per_query_limit = per_query_limit

    def discover(self, request: PlaylistRequest, queries: list[DiscoveryQuery]) -> list[CandidateTrack]:
        del request  # reserved for storefront/locale filters in a later sprint
        candidates: list[CandidateTrack] = []
        for query in queries:
            wanted_artist, wanted_title = wanted_match_fields(query)
            match = self.search.search_term(
                query.term,
                wanted_artist=wanted_artist,
                wanted_title=wanted_title,
                limit=self.per_query_limit,
            )
            if not match.found:
                continue
            candidates.append(candidate_from_itunes_match(match, query=query))
        return candidates
