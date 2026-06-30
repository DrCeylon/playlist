from __future__ import annotations

from enum import StrEnum


class EnergyCurveProfile(StrEnum):
    """UI-facing energy curve profiles (maps to planning.EnergyProfile in use cases)."""

    CHILL = "chill"
    STEADY = "steady"
    RISING = "rising"
    PARTY = "party"
    MAX_FROM_START = "max_from_start"
    RANDOM = "random"


class ExclusionKind(StrEnum):
    """Structured exclusion kinds exposed in the playlist builder form."""

    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"
    GENRE = "genre"
    MOOD = "mood"
    LANGUAGE = "language"


class ImportPhase(StrEnum):
    IDLE = "idle"
    RESOLVING = "resolving"
    ACQUIRING = "acquiring"
    WAITING_FOR_MANUAL_ACQUISITION = "waiting_for_manual_acquisition"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class ImportTrackStatus(StrEnum):
    PENDING = "pending"
    ADDED = "added"
    SKIPPED = "skipped"
    NOT_FOUND = "not_found"
    ERROR = "error"
    ACQUIRING = "acquiring"


class DiagnosticLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
