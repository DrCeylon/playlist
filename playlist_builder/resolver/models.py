from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.core.models import TrackRef
from playlist_builder.resolver.query import QueryVariant


@dataclass(frozen=True)
class ResolverCandidate:
    """Candidate returned by Apple Music search before final selection."""

    wanted: TrackRef
    artist: str
    title: str
    persistent_id: str = ""
    query: QueryVariant | None = None
    score: int = 0

    @property
    def label(self) -> str:
        return f"{self.artist} - {self.title}"


@dataclass(frozen=True)
class ResolverDecision:
    wanted: TrackRef
    selected: ResolverCandidate | None
    candidates: tuple[ResolverCandidate, ...]

    @property
    def found(self) -> bool:
        return self.selected is not None

    @property
    def confidence(self) -> int:
        return self.selected.score if self.selected else 0
