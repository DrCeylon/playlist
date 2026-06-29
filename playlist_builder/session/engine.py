from __future__ import annotations

from playlist_builder.discovery.models import merge_candidate_tracks
from playlist_builder.discovery.pipeline import DiscoveryPipeline
from playlist_builder.planning.analyzer import PlaylistAnalyzer
from playlist_builder.planning.models import CandidateTrack, PlaylistRequest
from playlist_builder.planning.planner import PlaylistPlanner
from playlist_builder.planning.report import build_mad_scientist_report
from playlist_builder.session.models import GenerationSession


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
        discovery_result = self.discovery.discover(request)
        discovered = list(discovery_result.pool.candidates)
        extras = list(extra_candidates or [])

        # Seeds are merged last so reference tracks always win deduplication.
        candidates = merge_candidate_lists(discovered, extras, seed_candidates)

        generated = self.planner.plan(request, candidates)
        analyzer = PlaylistAnalyzer()
        analysis = analyzer.analyze(generated)
        report = build_mad_scientist_report(generated, analysis=analysis)

        return GenerationSession(
            request=request,
            discovery_result=discovery_result,
            generated_playlist=generated,
            analysis=analysis,
            report=report,
        )
