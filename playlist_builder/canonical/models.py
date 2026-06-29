from __future__ import annotations

from dataclasses import dataclass, field

from playlist_builder.canonical.constants import DEFAULT_PLAYLIST_DESCRIPTION
from playlist_builder.canonical.enums import ImportStatus, ResolutionDecision
from playlist_builder.canonical.identity import track_identity_key


@dataclass(frozen=True, slots=True)
class CanonicalArtist:
    name: str
    sort_name: str = ""

    @property
    def display_name(self) -> str:
        return self.name.strip()


@dataclass(frozen=True, slots=True)
class CanonicalAlbum:
    title: str
    artist: CanonicalArtist
    release_year: int | None = None


@dataclass(frozen=True, slots=True)
class CanonicalTrack:
    """Universal musical identity — never contains provider-specific identifiers."""

    artist: CanonicalArtist
    title: str
    album: CanonicalAlbum | None = None
    duration_ms: int | None = None
    explicit: bool = False
    genres: tuple[str, ...] = ()
    isrc: str | None = None

    @property
    def identity_key(self) -> str:
        return track_identity_key(self.artist.name, self.title, isrc=self.isrc)

    @property
    def label(self) -> str:
        return f"{self.artist.display_name} - {self.title.strip()}"


@dataclass(frozen=True, slots=True)
class CanonicalPlaylistSection:
    name: str
    tracks: tuple[CanonicalTrack, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalPlaylist:
    name: str
    sections: tuple[CanonicalPlaylistSection, ...]
    description: str = DEFAULT_PLAYLIST_DESCRIPTION

    @property
    def tracks(self) -> tuple[CanonicalTrack, ...]:
        return tuple(track for section in self.sections for track in section.tracks)


@dataclass(frozen=True, slots=True)
class CanonicalCandidate:
    track: CanonicalTrack
    source: str
    provider_hints: tuple[str, ...] = ()
    raw_confidence: float = 0.0
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalSearchRequest:
    query: str
    limit: int = 10
    country_code: str = "us"


@dataclass(frozen=True, slots=True)
class CanonicalSearchResponse:
    request: CanonicalSearchRequest
    candidates: tuple[CanonicalCandidate, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalResolution:
    requested: CanonicalTrack
    selected: CanonicalCandidate | None
    confidence: float
    decision: ResolutionDecision
    alternatives: tuple[CanonicalCandidate, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalImportResult:
    track: CanonicalTrack
    status: ImportStatus
    section_name: str = "Playlist"
    error: str = ""


@dataclass(frozen=True, slots=True)
class CanonicalImportReport:
    playlist_name: str
    results: tuple[CanonicalImportResult, ...] = field(default_factory=tuple)
