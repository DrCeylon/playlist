from __future__ import annotations

from dataclasses import dataclass, field

from playlist_builder.core.models import TrackRef
from playlist_builder.planning.models import CandidateTrack, PlaylistRequest


@dataclass(frozen=True)
class DiscoveryQuery:
    """A concrete search query derived from a PlaylistRequest."""

    term: str
    source: str
    weight: float = 1.0


@dataclass(frozen=True)
class CandidatePool:
    """Raw and normalized candidates discovered for a playlist request."""

    request: PlaylistRequest
    candidates: tuple[CandidateTrack, ...]
    queries: tuple[DiscoveryQuery, ...] = ()

    @property
    def size(self) -> int:
        return len(self.candidates)

    def deduplicated(self) -> "CandidatePool":
        by_key: dict[str, CandidateTrack] = {}
        for candidate in self.candidates:
            existing = by_key.get(candidate.track.key)
            if existing is None or candidate.score > existing.score:
                by_key[candidate.track.key] = candidate
        return CandidatePool(
            request=self.request,
            candidates=tuple(by_key.values()),
            queries=self.queries,
        )


@dataclass(frozen=True)
class DiscoveryResult:
    pool: CandidatePool
    provider_stats: dict[str, int] = field(default_factory=dict)

    @property
    def candidate_count(self) -> int:
        return self.pool.size
