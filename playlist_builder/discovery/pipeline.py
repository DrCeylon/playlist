from __future__ import annotations

from playlist_builder.discovery.models import CandidatePool, DiscoveryResult
from playlist_builder.discovery.providers import CandidateProvider
from playlist_builder.discovery.query_builder import build_discovery_queries
from playlist_builder.planning.models import CandidateTrack, PlaylistRequest


class DiscoveryPipeline:
    """Runs candidate providers and returns a normalized CandidatePool."""

    def __init__(self, providers: list[CandidateProvider]) -> None:
        self.providers = providers

    def discover(self, request: PlaylistRequest) -> DiscoveryResult:
        queries = build_discovery_queries(request)
        all_candidates: list[CandidateTrack] = []
        stats: dict[str, int] = {}

        for provider in self.providers:
            candidates = provider.discover(request, queries)
            stats[provider.name] = len(candidates)
            all_candidates.extend(candidates)

        pool = CandidatePool(
            request=request,
            candidates=tuple(all_candidates),
            queries=tuple(queries),
        ).deduplicated()

        return DiscoveryResult(pool=pool, provider_stats=stats)
