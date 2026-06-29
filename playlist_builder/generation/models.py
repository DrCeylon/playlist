from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from playlist_builder.core.models import TrackRef


class EnergyProfile(str, Enum):
    CONSTANT = "constant"
    RISING = "rising"
    WAVE = "wave"


@dataclass(frozen=True)
class GenerationConstraint:
    excluded_styles: tuple[str, ...] = ()
    preferred_languages: tuple[str, ...] = ()
    target_track_count: int | None = None
    target_duration_minutes: int | None = None
    energy_profile: EnergyProfile = EnergyProfile.RISING


@dataclass(frozen=True)
class PlaylistRequest:
    name: str
    seed_tracks: tuple[TrackRef, ...]
    constraints: GenerationConstraint = field(default_factory=GenerationConstraint)
    description: str = ""


@dataclass(frozen=True)
class PlaylistCandidate:
    track: TrackRef
    score: float
    reason: str = ""
    source: str = "manual"


@dataclass(frozen=True)
class GeneratedPlaylist:
    request: PlaylistRequest
    tracks: tuple[TrackRef, ...]
    candidates: tuple[PlaylistCandidate, ...] = ()
