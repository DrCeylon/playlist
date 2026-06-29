from __future__ import annotations

from playlist_builder.core.models import TrackRef
from playlist_builder.planning.models import CandidateTrack, GeneratedPlaylist, PlaylistRequest
from playlist_builder.planning.scoring import rank_candidates


class PlaylistPlanner:
    """Builds a generated playlist from candidate tracks.

    Phase 2 starts with deterministic planning. Candidate discovery will be added
    behind this contract later, so the future UI can already target this API.
    """

    def plan(self, request: PlaylistRequest, candidates: list[CandidateTrack]) -> GeneratedPlaylist:
        request.validate()
        ranked = rank_candidates(candidates, request.constraints)
        limited = self._limit(ranked, request)
        return GeneratedPlaylist(request=request, candidates=tuple(limited))

    def seed_candidates(self, request: PlaylistRequest) -> list[CandidateTrack]:
        request.validate()
        return [
            CandidateTrack(
                track=seed.track,
                score=100.0 * seed.weight,
                source="seed",
                reasons=("seed",),
            )
            for seed in request.seeds
        ]

    def plan_from_seeds_only(self, request: PlaylistRequest) -> GeneratedPlaylist:
        return self.plan(request, self.seed_candidates(request))

    @staticmethod
    def _limit(candidates: list[CandidateTrack], request: PlaylistRequest) -> list[CandidateTrack]:
        target = request.constraints.target_track_count
        if target is None:
            # Phase 2 approximation: 3.5 minutes per track until real durations are available.
            target = max(1, round((request.constraints.target_duration_minutes or 0) / 3.5))
        return candidates[:target]
