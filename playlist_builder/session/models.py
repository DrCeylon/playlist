from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from playlist_builder.discovery.models import CandidatePool, DiscoveryResult
from playlist_builder.planning.analyzer import PlaylistAnalysis
from playlist_builder.planning.models import GeneratedPlaylist, PlaylistRequest


@dataclass(frozen=True)
class GenerationSession:
    """Full aggregate for a playlist generation attempt.

    This object is intentionally larger than GeneratedPlaylist: it can be saved,
    reopened, compared, displayed in a future UI, or synced to an iPhone/iPad app.
    """

    request: PlaylistRequest
    generated_playlist: GeneratedPlaylist
    discovery_result: DiscoveryResult | None = None
    analysis: PlaylistAnalysis | None = None
    report: str = ""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def candidate_pool(self) -> CandidatePool | None:
        return self.discovery_result.pool if self.discovery_result else None
