from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.canonical.enums import ConfidenceLevel, ProviderId
from playlist_builder.ui.shared.dto.enums import EnergyCurveProfile, ExclusionKind


@dataclass(frozen=True, slots=True)
class SeedReference:
    artist: str = ""
    title: str = ""
    weight: float = 1.0

    @property
    def label(self) -> str:
        artist = self.artist.strip()
        title = self.title.strip()
        if artist and title:
            return f"{artist} — {title}"
        return artist or title


@dataclass(frozen=True, slots=True)
class EnergyCurveOption:
    profile: EnergyCurveProfile = EnergyCurveProfile.RISING
    chapter_labels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExclusionRule:
    kind: ExclusionKind
    value: str
    reason: str = ""


@dataclass(frozen=True, slots=True)
class PlaylistGenerationRequest:
    name: str
    provider_id: ProviderId
    seeds: tuple[SeedReference, ...] = ()
    keywords: tuple[str, ...] = ()
    description: str = ""
    target_track_count: int | None = None
    target_duration_minutes: int | None = None
    energy_curve: EnergyCurveOption = EnergyCurveOption()
    exclusions: tuple[ExclusionRule, ...] = ()
    playlist_theme: str = ""


@dataclass(frozen=True, slots=True)
class GeneratedTrackPreview:
    artist: str
    title: str
    section: str
    score: float
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: str = ""


@dataclass(frozen=True, slots=True)
class GeneratedSectionPreview:
    name: str
    tracks: tuple[GeneratedTrackPreview, ...] = ()


@dataclass(frozen=True, slots=True)
class PlaylistGenerationResult:
    playlist_name: str
    sections: tuple[GeneratedSectionPreview, ...] = ()
    average_score: float = 0.0
    provider_id: ProviderId = ProviderId.APPLE_MUSIC

    @property
    def track_count(self) -> int:
        return sum(len(section.tracks) for section in self.sections)
