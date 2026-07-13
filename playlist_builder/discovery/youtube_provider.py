from __future__ import annotations

from playlist_builder.canonical.models import CanonicalCandidate
from playlist_builder.discovery.models import DiscoveryCandidate, DiscoveryQuery
from playlist_builder.discovery.probe import wanted_match_fields
from playlist_builder.discovery.providers import CandidateProvider
from playlist_builder.integration.youtube_music.catalog import YouTubeMusicCatalogGateway


def discovery_candidate_from_youtube(
    candidate: CanonicalCandidate,
    *,
    query: DiscoveryQuery,
) -> DiscoveryCandidate:
    return DiscoveryCandidate(
        track=candidate.track,
        score=max(1.0, 40.0 * query.weight),
        source=candidate.source_label or candidate.provider_id.value,
        reasons=(*candidate.reasons, f"query:{query.source}:{query.term}"),
        album=candidate.track.album.title if candidate.track.album else "",
        genre=candidate.track.genres[0] if candidate.track.genres else "",
        explicit=candidate.track.explicit,
        provider_id=candidate.provider_id,
        catalog_url=candidate.provider_hints[0] if candidate.provider_hints else "",
    )


class YouTubeCandidateProvider(CandidateProvider):
    """Candidate provider backed by the YouTube Music catalog gateway."""

    name = "youtube_music"

    def __init__(self, catalog: YouTubeMusicCatalogGateway, per_query_limit: int = 10) -> None:
        self.catalog = catalog
        self.per_query_limit = per_query_limit

    def discover(self, request, queries: list[DiscoveryQuery]) -> list[DiscoveryCandidate]:
        del request
        from playlist_builder.canonical.models import CanonicalSearchRequest

        candidates: list[DiscoveryCandidate] = []
        for query in queries:
            wanted_artist, wanted_title = wanted_match_fields(query)
            response = self.catalog.search(
                CanonicalSearchRequest(
                    query=query.term,
                    limit=self.per_query_limit,
                    wanted_artist=wanted_artist,
                    wanted_title=wanted_title,
                )
            )
            if not response.candidates:
                continue
            seen_keys: set[str] = set()
            for hit in response.candidates:
                candidate = discovery_candidate_from_youtube(hit, query=query)
                key = candidate.track.identity_key
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                candidates.append(candidate)
        return candidates
