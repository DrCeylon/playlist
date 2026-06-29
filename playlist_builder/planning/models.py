from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from playlist_builder.canonical.constants import DEFAULT_PLAYLIST_DESCRIPTION
from playlist_builder.core.models import TrackRef


class EnergyProfile(str, Enum):
    """Energy curves available in the first generated-playlist sprint."""

    CHILL = "chill"
    STEADY = "steady"
    RISING = "rising"
    PARTY = "party"
    MAX_FROM_START = "max_from_start"
    RANDOM = "random"


class ConstraintKind(str, Enum):
    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"
    GENRE = "genre"
    MOOD = "mood"
    LANGUAGE = "language"
    TERM = "term"


@dataclass(frozen=True)
class SeedTrack:
    track: TrackRef
    weight: float = 1.0


@dataclass(frozen=True)
class ExclusionRule:
    """User-defined exclusion.

    The UI will eventually expose these as repeatable fields. The engine keeps
    them explicit rather than hiding them in a single free-text list.
    """

    kind: ConstraintKind
    value: str
    reason: str = ""

    def validate(self) -> None:
        if not self.value.strip():
            raise ValueError("Une exclusion doit avoir une valeur non vide.")


@dataclass(frozen=True)
class InclusionRule:
    kind: ConstraintKind
    value: str
    weight: float = 1.0

    def validate(self) -> None:
        if not self.value.strip():
            raise ValueError("Une inclusion doit avoir une valeur non vide.")
        if self.weight <= 0:
            raise ValueError("Le poids d'une inclusion doit être positif.")


@dataclass(frozen=True)
class GenerationConstraints:
    target_track_count: int | None = None
    target_duration_minutes: int | None = None
    energy_profile: EnergyProfile = EnergyProfile.RISING

    # Backward-compatible simple lists used by the current CLI/tests.
    excluded_terms: tuple[str, ...] = ()
    preferred_terms: tuple[str, ...] = ()

    # Sprint 2 product target: structured repeatable exclusions/inclusions.
    exclusions: tuple[ExclusionRule, ...] = ()
    inclusions: tuple[InclusionRule, ...] = ()

    allow_explicit: bool = True
    quality_over_quantity: bool = True

    def validate(self) -> None:
        if self.target_track_count is None and self.target_duration_minutes is None:
            raise ValueError("Une génération doit définir un nombre de morceaux ou une durée cible.")
        if self.target_track_count is not None and self.target_track_count <= 0:
            raise ValueError("Le nombre de morceaux cible doit être positif.")
        if self.target_duration_minutes is not None and self.target_duration_minutes <= 0:
            raise ValueError("La durée cible doit être positive.")
        for exclusion in self.exclusions:
            exclusion.validate()
        for inclusion in self.inclusions:
            inclusion.validate()


@dataclass(frozen=True)
class PlaylistRequest:
    name: str
    seeds: tuple[SeedTrack, ...]
    constraints: GenerationConstraints
    description: str = DEFAULT_PLAYLIST_DESCRIPTION

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Le nom de la playlist est obligatoire.")
        if not self.seeds:
            raise ValueError("Au moins un morceau de référence est requis.")
        self.constraints.validate()


@dataclass(frozen=True)
class CandidateTrack:
    track: TrackRef
    score: float
    source: str = "unknown"
    reasons: tuple[str, ...] = field(default_factory=tuple)
    album: str = ""
    genre: str = ""
    mood: str = ""
    language: str = ""
    energy: float | None = None
    explicit: bool = False

    @property
    def searchable_text(self) -> str:
        return " ".join(
            value
            for value in (
                self.track.artist,
                self.track.title,
                self.album,
                self.genre,
                self.mood,
                self.language,
            )
            if value
        ).lower()


@dataclass(frozen=True)
class GeneratedPlaylist:
    request: PlaylistRequest
    candidates: tuple[CandidateTrack, ...]
    rejected: tuple[CandidateTrack, ...] = ()
    suggestions: tuple[CandidateTrack, ...] = ()

    @property
    def tracks(self) -> list[TrackRef]:
        return [candidate.track for candidate in self.candidates]
