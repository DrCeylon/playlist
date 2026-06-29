from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from playlist_builder.canonical.compat import canonical_track_from_legacy, legacy_track_from_canonical
from playlist_builder.canonical.constants import DEFAULT_PLAYLIST_DESCRIPTION
from playlist_builder.canonical.identity import track_identity_key
from playlist_builder.canonical.models import CanonicalTrack

# Backward-compatible alias — new code should import from canonical.constants.
LEGACY_DEFAULT_PLAYLIST_DESCRIPTION = DEFAULT_PLAYLIST_DESCRIPTION


@dataclass(frozen=True)
class TrackRef:
    """Legacy playlist track reference used by current CLIs and JSON import.

    New features should prefer :class:`~playlist_builder.canonical.models.CanonicalTrack`
    and convert at integration boundaries via :meth:`to_canonical`.
    """

    artist: str
    title: str
    section: str = "Playlist"

    @property
    def key(self) -> str:
        return track_identity_key(self.artist, self.title)

    @property
    def label(self) -> str:
        return f"{self.artist} - {self.title}"

    def to_canonical(self) -> CanonicalTrack:
        return canonical_track_from_legacy(self)

    @classmethod
    def from_canonical(cls, track: CanonicalTrack, *, section: str = "Playlist") -> TrackRef:
        return legacy_track_from_canonical(track, section=section)


@dataclass(frozen=True)
class PlaylistSection:
    name: str
    tracks: tuple[TrackRef, ...]


@dataclass(frozen=True)
class PlaylistDefinition:
    name: str
    sections: tuple[PlaylistSection, ...]
    description: str = DEFAULT_PLAYLIST_DESCRIPTION

    @property
    def tracks(self) -> list[TrackRef]:
        return [track for section in self.sections for track in section.tracks]

    def to_canonical(self):
        from playlist_builder.canonical.compat import canonical_playlist_from_legacy

        return canonical_playlist_from_legacy(self)


@dataclass(frozen=True)
class CatalogMatch:
    query: TrackRef
    matched_artist: str = ""
    matched_title: str = ""
    url: str = ""
    raw: dict[str, Any] | None = None
    error: str = ""

    @property
    def found(self) -> bool:
        return bool(self.url)


class TrackAddStatus(str, Enum):
    ADDED = "added"
    NOT_FOUND = "not_found"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass(frozen=True)
class TrackAddResult:
    track: TrackRef
    status: TrackAddStatus
    error: str = ""
