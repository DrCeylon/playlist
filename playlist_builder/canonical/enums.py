from __future__ import annotations

from enum import StrEnum


class ProviderId(StrEnum):
    """Stable provider identifiers used by the integration gateway registry."""

    APPLE_MUSIC = "apple_music"
    APPLE_MUSICKIT = "apple_musickit"
    SPOTIFY = "spotify"
    YOUTUBE_MUSIC = "youtube_music"
    DEEZER = "deezer"
    DISCOGS = "discogs"
    MUSICBRAINZ = "musicbrainz"


class ProviderCapability(StrEnum):
    """Capabilities a provider gateway may expose."""

    CATALOG_SEARCH = "catalog_search"
    LIBRARY_RESOLVE = "library_resolve"
    PLAYLIST_DELIVERY = "playlist_delivery"


class ResolutionDecision(StrEnum):
    ACCEPTED = "accepted"
    AMBIGUOUS = "ambiguous"
    REJECTED = "rejected"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_score(cls, score: float) -> ConfidenceLevel:
        if score >= 80:
            return cls.HIGH
        if score >= 55:
            return cls.MEDIUM
        return cls.LOW


class ImportStatus(StrEnum):
    ADDED = "added"
    NOT_FOUND = "not_found"
    SKIPPED = "skipped"
    ERROR = "error"
