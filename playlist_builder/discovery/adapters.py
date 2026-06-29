from __future__ import annotations

from playlist_builder.discovery.models import DiscoveryCandidate
from playlist_builder.integration.apple_music.mapper import discovery_candidate_to_planning
from playlist_builder.planning.models import CandidateTrack, merge_candidate_tracks


def discovery_candidates_to_planning(candidates: list[DiscoveryCandidate]) -> list[CandidateTrack]:
    return [discovery_candidate_to_planning(candidate) for candidate in candidates]


def merge_discovery_candidate_lists(*groups: list[DiscoveryCandidate]) -> list[DiscoveryCandidate]:
    from playlist_builder.discovery.models import merge_discovery_candidates

    by_key: dict[str, DiscoveryCandidate] = {}
    for group in groups:
        for candidate in group:
            existing = by_key.get(candidate.track.identity_key)
            if existing is None:
                by_key[candidate.track.identity_key] = candidate
            else:
                by_key[candidate.track.identity_key] = merge_discovery_candidates(existing, candidate)
    return list(by_key.values())


def merge_planning_candidate_lists(*groups: list[CandidateTrack]) -> list[CandidateTrack]:
    by_key: dict[str, CandidateTrack] = {}
    for group in groups:
        for candidate in group:
            existing = by_key.get(candidate.track.key)
            if existing is None:
                by_key[candidate.track.key] = candidate
            else:
                by_key[candidate.track.key] = merge_candidate_tracks(existing, candidate)
    return list(by_key.values())


def merge_planning_from_discovery_groups(*groups: list[DiscoveryCandidate]) -> list[CandidateTrack]:
    return merge_planning_candidate_lists(
        *[discovery_candidates_to_planning(group) for group in groups]
    )
