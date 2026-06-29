from __future__ import annotations

from abc import ABC, abstractmethod

from playlist_builder.core.models import TrackRef
from playlist_builder.discovery.models import DiscoveryQuery
from playlist_builder.planning.models import CandidateTrack, PlaylistRequest


class CandidateProvider(ABC):
    """Abstract provider for candidate discovery.

    Providers may use Apple/iTunes, a local catalog, MusicKit later, or a static
    fixture in tests. The generation engine only depends on this contract.
    """

    name = "provider"

    @abstractmethod
    def discover(self, request: PlaylistRequest, queries: list[DiscoveryQuery]) -> list[CandidateTrack]:
        raise NotImplementedError


class StaticCandidateProvider(CandidateProvider):
    name = "static"

    def __init__(self, tracks: list[CandidateTrack] | list[TrackRef]) -> None:
        self._tracks = tracks

    def discover(self, request: PlaylistRequest, queries: list[DiscoveryQuery]) -> list[CandidateTrack]:
        discovered: list[CandidateTrack] = []
        for item in self._tracks:
            if isinstance(item, CandidateTrack):
                discovered.append(item)
            else:
                discovered.append(CandidateTrack(track=item, score=10, source=self.name))
        return discovered
