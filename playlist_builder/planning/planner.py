from __future__ import annotations

from playlist_builder.planning.models import CandidateTrack, GeneratedPlaylist, PlaylistRequest
from playlist_builder.planning.scoring import is_rejected, rank_candidates

MIN_QUALITY_SCORE = 1.0
SUGGESTION_COUNT = 10


class PlaylistPlanner:
    """Builds a generated playlist from candidate tracks."""

    def plan(self, request: PlaylistRequest, candidates: list[CandidateTrack]) -> GeneratedPlaylist:
        request.validate()
        ranked = rank_candidates(candidates, request.constraints)
        rejected = tuple(candidate for candidate in ranked if is_rejected(candidate))
        eligible = [candidate for candidate in ranked if not is_rejected(candidate)]

        if request.constraints.quality_over_quantity:
            eligible = [candidate for candidate in eligible if candidate.score >= MIN_QUALITY_SCORE]

        selected = self._select_candidates(eligible, request)
        selected_keys = {candidate.track.key for candidate in selected}
        suggestions = tuple(
            candidate for candidate in eligible if candidate.track.key not in selected_keys
        )[:SUGGESTION_COUNT]

        return GeneratedPlaylist(
            request=request,
            candidates=tuple(selected),
            rejected=rejected,
            suggestions=suggestions,
        )

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
    def _target_count(request: PlaylistRequest) -> int:
        target = request.constraints.target_track_count
        if target is None:
            target = max(1, round((request.constraints.target_duration_minutes or 0) / 3.5))
        return target

    @staticmethod
    def _select_candidates(candidates: list[CandidateTrack], request: PlaylistRequest) -> list[CandidateTrack]:
        target = PlaylistPlanner._target_count(request)
        by_key = {candidate.track.key: candidate for candidate in candidates}

        selected: list[CandidateTrack] = []
        for seed in request.seeds:
            candidate = by_key.get(seed.track.key)
            if candidate is not None:
                selected.append(candidate)

        selected_keys = {candidate.track.key for candidate in selected}
        remaining = max(0, target - len(selected))
        for candidate in candidates:
            if candidate.track.key in selected_keys:
                continue
            selected.append(candidate)
            selected_keys.add(candidate.track.key)
            remaining -= 1
            if remaining == 0:
                break

        return selected[:target]
