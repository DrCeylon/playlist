from __future__ import annotations

from dataclasses import dataclass, field

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalTrack
from playlist_builder.planning.models import PlaylistRequest


@dataclass(frozen=True, slots=True)
class DiscoveryQuery:
    """A concrete search query derived from a PlaylistRequest."""

    term: str
    source: str
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class DiscoveryCandidate:
    """Provider-neutral discovery result before planning adaptation."""

    track: CanonicalTrack
    score: float
    source: str = "unknown"
    reasons: tuple[str, ...] = field(default_factory=tuple)
    album: str = ""
    genre: str = ""
    mood: str = ""
    language: str = ""
    energy: float | None = None
    explicit: bool = False
    provider_id: ProviderId = ProviderId.APPLE_MUSIC
    catalog_url: str = ""
    section: str = ""


def merge_discovery_candidates(existing: DiscoveryCandidate, incoming: DiscoveryCandidate) -> DiscoveryCandidate:
    winner, other = (incoming, existing) if incoming.score > existing.score else (existing, incoming)
    return DiscoveryCandidate(
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
        provider_id=winner.provider_id,
        catalog_url=winner.catalog_url or other.catalog_url,
        section=winner.section or other.section,
    )


@dataclass(frozen=True)
class CandidatePool:
    """Raw and normalized candidates discovered for a playlist request."""

    request: PlaylistRequest
    candidates: tuple[DiscoveryCandidate, ...]
    queries: tuple[DiscoveryQuery, ...] = ()

    @property
    def size(self) -> int:
        return len(self.candidates)

    def deduplicated(self) -> CandidatePool:
        by_key: dict[str, DiscoveryCandidate] = {}
        for candidate in self.candidates:
            existing = by_key.get(candidate.track.identity_key)
            if existing is None:
                by_key[candidate.track.identity_key] = candidate
            else:
                by_key[candidate.track.identity_key] = merge_discovery_candidates(existing, candidate)
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
