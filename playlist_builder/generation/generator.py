from __future__ import annotations

from playlist_builder.core.models import TrackRef
from playlist_builder.generation.models import GeneratedPlaylist, PlaylistCandidate, PlaylistRequest


class PlaylistGenerator:
    """Deterministic generator skeleton.

    Phase 2 intentionally starts with a safe, testable core:
    - no Apple Music side effects;
    - no deletion;
    - no external API dependency;
    - seed tracks are preserved first.

    Future iterations will plug similarity and catalog candidate providers here.
    """

    def build(self, request: PlaylistRequest, candidates: list[PlaylistCandidate] | None = None) -> GeneratedPlaylist:
        candidates = candidates or []
        ordered: list[TrackRef] = []
        seen: set[str] = set()

        for seed in request.seed_tracks:
            if seed.key not in seen:
                ordered.append(seed)
                seen.add(seed.key)

        sorted_candidates = sorted(candidates, key=lambda candidate: candidate.score, reverse=True)
        target = request.constraints.target_track_count

        for candidate in sorted_candidates:
            if candidate.track.key in seen:
                continue
            ordered.append(candidate.track)
            seen.add(candidate.track.key)
            if target is not None and len(ordered) >= target:
                break

        return GeneratedPlaylist(
            request=request,
            tracks=tuple(ordered),
            candidates=tuple(sorted_candidates),
        )
