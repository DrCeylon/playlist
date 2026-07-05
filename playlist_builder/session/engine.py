from __future__ import annotations

from dataclasses import replace

from playlist_builder.discovery.fulfillment import build_expansion_queries, explain_shortfall
from playlist_builder.discovery.pipeline import DiscoveryPipeline
from playlist_builder.planning.analyzer import PlaylistAnalyzer
from playlist_builder.planning.models import CandidateTrack, GeneratedPlaylist, PlaylistRequest, merge_candidate_tracks
from playlist_builder.planning.planner import PlaylistPlanner
from playlist_builder.planning.report import build_mad_scientist_report
from playlist_builder.planning.scoring import is_rejected, rank_candidates
from playlist_builder.session.models import GenerationSession

MAX_FULFILLMENT_PASSES = 3


def merge_candidate_lists(*groups: list[CandidateTrack]) -> list[CandidateTrack]:
    by_key: dict[str, CandidateTrack] = {}
    for group in groups:
        for candidate in group:
            existing = by_key.get(candidate.track.key)
            if existing is None:
                by_key[candidate.track.key] = candidate
            else:
                by_key[candidate.track.key] = merge_candidate_tracks(existing, candidate)
    return list(by_key.values())


class GenerationSessionEngine:
    """Orchestrates discovery, planning, analysis and reporting."""

    def __init__(self, discovery: DiscoveryPipeline, planner: PlaylistPlanner | None = None) -> None:
        self.discovery = discovery
        self.planner = planner or PlaylistPlanner()

    def generate(self, request: PlaylistRequest, extra_candidates: list[CandidateTrack] | None = None) -> GenerationSession:
        seed_candidates = self.planner.seed_candidates(request)
        target = PlaylistPlanner._target_count(request)
        extras = list(extra_candidates or [])
        discovered_candidates: list[CandidateTrack] = []
        discovery_result = None
        generated: GeneratedPlaylist | None = None
        passes_used = 0

        for pass_index in range(MAX_FULFILLMENT_PASSES):
            passes_used = pass_index + 1
            if pass_index == 0:
                discovery_result = self.discovery.discover(request)
            else:
                expansion_queries = build_expansion_queries(request, pass_index=pass_index - 1)
                if not expansion_queries:
                    break
                discovery_result = self._discover_with_queries(request, expansion_queries)

            batch = DiscoveryPipeline.to_planning_candidates(discovery_result)
            discovered_candidates = merge_candidate_lists(discovered_candidates, batch)

            planning_request = request
            if pass_index >= 1:
                planning_request = replace(
                    request,
                    constraints=replace(request.constraints, quality_over_quantity=False),
                )

            candidates = merge_candidate_lists(discovered_candidates, extras, seed_candidates)
            generated = self.planner.plan(planning_request, candidates)
            if len(generated.candidates) >= target:
                generated = self._with_shortfall_metadata(
                    generated,
                    request,
                    discovered_count=len(discovered_candidates),
                    passes_used=passes_used,
                    shortfall_message="",
                )
                break

        if generated is None:
            raise RuntimeError("Generation produced no result.")

        if len(generated.candidates) < target:
            generated = self._with_shortfall_metadata(
                generated,
                request,
                discovered_count=len(discovered_candidates),
                passes_used=passes_used,
            )

        analyzer = PlaylistAnalyzer()
        analysis = analyzer.analyze(generated)
        report = build_mad_scientist_report(generated, analysis=analysis)

        assert discovery_result is not None
        return GenerationSession(
            request=request,
            discovery_result=discovery_result,
            generated_playlist=generated,
            analysis=analysis,
            report=report,
        )

    def _discover_with_queries(self, request: PlaylistRequest, queries):
        from playlist_builder.discovery.models import CandidatePool, DiscoveryResult

        all_candidates = []
        stats: dict[str, int] = {}
        for provider in self.discovery.providers:
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

    def _with_shortfall_metadata(
        self,
        generated: GeneratedPlaylist,
        request: PlaylistRequest,
        *,
        discovered_count: int,
        passes_used: int,
        shortfall_message: str | None = None,
    ) -> GeneratedPlaylist:
        target = PlaylistPlanner._target_count(request)
        ranked = rank_candidates(
            merge_candidate_lists(
                list(generated.candidates),
                list(generated.suggestions),
                list(generated.rejected),
            ),
            request.constraints,
        )
        rejected_count = sum(1 for candidate in ranked if is_rejected(candidate))
        eligible_count = sum(1 for candidate in ranked if not is_rejected(candidate))

        message = shortfall_message
        if message is None:
            message = explain_shortfall(
                request,
                target=target,
                selected=len(generated.candidates),
                discovered=discovered_count,
                eligible=eligible_count,
                rejected=rejected_count,
                passes_used=passes_used,
            )
        elif not message and len(generated.candidates) >= target:
            message = ""

        return GeneratedPlaylist(
            request=generated.request,
            candidates=generated.candidates,
            rejected=generated.rejected,
            suggestions=generated.suggestions,
            shortfall_message=message,
            discovery_passes=passes_used,
        )
