from __future__ import annotations

from playlist_builder.catalog.apple_search import AppleCatalogSearch
from playlist_builder.discovery.models import DiscoveryQuery
from playlist_builder.discovery.providers import CandidateProvider
from playlist_builder.planning.models import CandidateTrack, PlaylistRequest
from playlist_builder.core.models import TrackRef


class ITunesCandidateProvider(CandidateProvider):
    """Candidate provider backed by the public iTunes Search catalog.

    This is conservative: it uses the existing catalog client and converts found
    matches into CandidateTrack objects. It does not modify Apple Music.
    """

    name = "itunes"

    def __init__(self, search: AppleCatalogSearch, per_query_limit: int = 10) -> None:
        self.search = search
        self.per_query_limit = per_query_limit

    def discover(self, request: PlaylistRequest, queries: list[DiscoveryQuery]) -> list[CandidateTrack]:
        candidates: list[CandidateTrack] = []
        for query in queries:
            # The current AppleCatalogSearch is track-oriented. We start by
            # searching the query term as a broad TrackRef; a later iteration can
            # add a native multi-result search method.
            probe = TrackRef(artist=query.term, title=query.term, section="Discovery")
            match = self.search.search_track(probe, limit=self.per_query_limit)
            if not match.found:
                continue
            artist = match.matched_artist or query.term
            title = match.matched_title or query.term
            candidates.append(
                CandidateTrack(
                    track=TrackRef(artist=artist, title=title, section="Discovery"),
                    score=max(1.0, 40.0 * query.weight),
                    source=self.name,
                    reasons=(f"query:{query.source}:{query.term}",),
                )
            )
        return candidates
