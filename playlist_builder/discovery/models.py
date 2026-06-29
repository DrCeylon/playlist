from __future__ import annotations

from dataclasses import dataclass, field

from playlist_builder.planning.models import CandidateTrack, PlaylistRequest


@dataclass(frozen=True)
class DiscoveryQuery:
    """A concrete search query derived from a PlaylistRequest."""

    term: str
    source: str
    weight: float = 1.0


def merge_candidate_tracks(existing: CandidateTrack, incoming: CandidateTrack) -> CandidateTrack:
    winner, other = (incoming, existing) if incoming.score > existing.score else (existing, incoming)
    return CandidateTrack(
        track=winner.track,
        score=winner.score,
        source=winner.source,
        reasons=tuple(dict.fromkeys((*winner.reasons, *other.reasons))),
        album=winner.album or other.album,
        genre=winner.genre or other.genre,
        mood=winner.mood or other.mood,
        language=winner.language or other.language,
        energy=winner.energy if winner.energy is not None else other.energy,
        explicit=winner.explicit or other.explicit,
    )


@dataclass(frozen=True)
class CandidatePool:
    """Raw and normalized candidates discovered for a playlist request."""

    request: PlaylistRequest
    candidates: tuple[CandidateTrack, ...]
    queries: tuple[DiscoveryQuery, ...] = ()

    @property
    def size(self) -> int:
        return len(self.candidates)

    def deduplicated(self) -> CandidatePool:
        by_key: dict[str, CandidateTrack] = {}
        for candidate in self.candidates:
            existing = by_key.get(candidate.track.key)
            if existing is None:
                by_key[candidate.track.key] = candidate
            else:
                by_key[candidate.track.key] = merge_candidate_tracks(existing, candidate)
        return CandidatePool(
            request=self.request,
            candidates=tuple(by_key.values()),
            queries=self.queries,
        )


@dataclass(frozen=True)
class DiscoveryResult:
    pool: CandidatePool
    provider_stats: dict[str, int] = field(default_factory=dict)
    deduplicated_count: int = 0

    @property
    def candidate_count(self) -> int:
        return self.pool.size
