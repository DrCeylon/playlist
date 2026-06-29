from __future__ import annotations

from playlist_builder.discovery.adapters import discovery_candidates_to_planning
from playlist_builder.discovery.models import CandidatePool, DiscoveryResult
from playlist_builder.discovery.providers import CandidateProvider
from playlist_builder.discovery.query_builder import build_discovery_queries
from playlist_builder.planning.models import PlaylistRequest


class DiscoveryPipeline:
    """Runs candidate providers and returns a normalized CandidatePool."""

    def __init__(self, providers: list[CandidateProvider]) -> None:
        self.providers = providers

    def discover(self, request: PlaylistRequest) -> DiscoveryResult:
        queries = build_discovery_queries(request)
        all_candidates = []
        stats: dict[str, int] = {}

        for provider in self.providers:
            discovered = provider.discover(request, queries)
            stats[provider.name] = len(discovered)
            all_candidates.extend(discovered)

        raw_pool = CandidatePool(
            request=request,
            candidates=tuple(all_candidates),
            queries=tuple(queries),
        )
        pool = raw_pool.deduplicated()

        return DiscoveryResult(
            pool=pool,
            provider_stats=stats,
            deduplicated_count=pool.size,
        )

    @staticmethod
    def to_planning_candidates(result: DiscoveryResult):
        return discovery_candidates_to_planning(list(result.pool.candidates))
