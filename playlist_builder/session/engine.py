from __future__ import annotations

from playlist_builder.discovery.pipeline import DiscoveryPipeline
from playlist_builder.planning.analyzer import PlaylistAnalyzer
from playlist_builder.planning.models import CandidateTrack, PlaylistRequest
from playlist_builder.planning.planner import PlaylistPlanner
from playlist_builder.planning.report import build_mad_scientist_report
from playlist_builder.session.models import GenerationSession


class GenerationSessionEngine:
    """Orchestrates discovery, planning, analysis and reporting."""

    def __init__(self, discovery: DiscoveryPipeline, planner: PlaylistPlanner | None = None) -> None:
        self.discovery = discovery
        self.planner = planner or PlaylistPlanner()

    def generate(self, request: PlaylistRequest, extra_candidates: list[CandidateTrack] | None = None) -> GenerationSession:
        discovery_result = self.discovery.discover(request)
        candidates = list(discovery_result.pool.candidates)
        if extra_candidates:
            candidates.extend(extra_candidates)

        generated = self.planner.plan(request, candidates)
        analysis = PlaylistAnalyzer().analyze(generated)
        report = build_mad_scientist_report(generated)

        return GenerationSession(
            request=request,
            discovery_result=discovery_result,
            generated_playlist=generated,
            analysis=analysis,
            report=report,
        )
