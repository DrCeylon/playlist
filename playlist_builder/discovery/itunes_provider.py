from __future__ import annotations

from playlist_builder.canonical.contracts import CatalogSearchPort
from playlist_builder.canonical.models import CanonicalSearchRequest
from playlist_builder.discovery.models import DiscoveryCandidate, DiscoveryQuery
from playlist_builder.discovery.probe import wanted_match_fields
from playlist_builder.discovery.providers import CandidateProvider
from playlist_builder.integration.apple_music.mapper import discovery_candidate_from_canonical
from playlist_builder.planning.models import PlaylistRequest


class ITunesCandidateProvider(CandidateProvider):
    """Candidate provider backed by the Apple Music catalog gateway."""

    name = "itunes"

    def __init__(self, catalog: CatalogSearchPort, per_query_limit: int = 10, *, country_code: str = "us") -> None:
        self.catalog = catalog
        self.per_query_limit = per_query_limit
        self.country_code = country_code

    def discover(self, request: PlaylistRequest, queries: list[DiscoveryQuery]) -> list[DiscoveryCandidate]:
        del request
        candidates: list[DiscoveryCandidate] = []
        for query in queries:
            wanted_artist, wanted_title = wanted_match_fields(query)
            response = self.catalog.search(
                CanonicalSearchRequest(
                    query=query.term,
                    limit=self.per_query_limit,
                    country_code=self.country_code,
                    wanted_artist=wanted_artist,
                    wanted_title=wanted_title,
                )
            )
            if not response.candidates:
                continue
            candidates.append(
                discovery_candidate_from_canonical(response.candidates[0], query=query)
            )
        return candidates


def candidate_from_itunes_match(match, *, query: DiscoveryQuery, source: str = "itunes"):
    from playlist_builder.canonical.models import CanonicalArtist, CanonicalCandidate, CanonicalTrack
    from playlist_builder.planning.models import CandidateTrack

    raw = match.raw or {}
    artist = match.matched_artist or query.term
    title = match.matched_title or query.term
    canonical = CanonicalCandidate(
        track=CanonicalTrack(
            artist=CanonicalArtist(name=artist),
            title=title,
            explicit=raw.get("trackExplicitness", "") == "explicit",
            genres=(str(raw.get("primaryGenreName", "")),) if raw.get("primaryGenreName") else (),
        ),
        source=source,
        provider_hints=(match.url,) if match.url else (),
        raw_confidence=100.0,
    )
    planning = discovery_candidate_from_canonical(
        canonical,
        query=query,
        album=str(raw.get("collectionName", "")),
        genre=str(raw.get("primaryGenreName", "")),
    )
    from playlist_builder.discovery.adapters import discovery_candidate_to_planning

    return discovery_candidate_to_planning(planning)
