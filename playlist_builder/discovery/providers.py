from __future__ import annotations

from abc import ABC, abstractmethod

from playlist_builder.core.models import TrackRef
from playlist_builder.discovery.models import DiscoveryCandidate, DiscoveryQuery
from playlist_builder.planning.models import CandidateTrack, PlaylistRequest


class CandidateProvider(ABC):
    """Abstract provider for candidate discovery.

    Providers return provider-neutral :class:`DiscoveryCandidate` values.
    Planning adaptation happens at the discovery pipeline boundary.
    """

    name = "provider"

    @abstractmethod
    def discover(self, request: PlaylistRequest, queries: list[DiscoveryQuery]) -> list[DiscoveryCandidate]:
        raise NotImplementedError


class StaticCandidateProvider(CandidateProvider):
    name = "static"

    def __init__(self, tracks: list[CandidateTrack] | list[TrackRef] | list[DiscoveryCandidate]) -> None:
        self._tracks = tracks

    def discover(self, request: PlaylistRequest, queries: list[DiscoveryQuery]) -> list[DiscoveryCandidate]:
        from playlist_builder.canonical.compat import canonical_track_from_legacy
        from playlist_builder.canonical.enums import ProviderId
        from playlist_builder.discovery.models import DiscoveryCandidate

        del request, queries
        discovered: list[DiscoveryCandidate] = []
        for item in self._tracks:
            if isinstance(item, DiscoveryCandidate):
                discovered.append(item)
            elif isinstance(item, CandidateTrack):
                discovered.append(
                    DiscoveryCandidate(
                        track=canonical_track_from_legacy(item.track),
                        score=item.score,
                        source=item.source,
                        reasons=item.reasons,
                        album=item.album,
                        genre=item.genre,
                        mood=item.mood,
                        language=item.language,
                        energy=item.energy,
                        explicit=item.explicit,
                        provider_id=ProviderId.APPLE_MUSIC,
                        section=item.track.section,
                    )
                )
            else:
                discovered.append(
                    DiscoveryCandidate(
                        track=canonical_track_from_legacy(item),
                        score=10.0,
                        source=self.name,
                        section=item.section,
                    )
                )
        return discovered
