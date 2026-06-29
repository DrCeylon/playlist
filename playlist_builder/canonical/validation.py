from __future__ import annotations

from playlist_builder.canonical.models import (
    CanonicalPlaylist,
    CanonicalSearchRequest,
    CanonicalTrack,
)


class ValidationError(ValueError):
    """Raised when canonical domain invariants are violated."""


def validate_track(track: CanonicalTrack) -> None:
    if not track.artist.name.strip():
        raise ValidationError("CanonicalTrack.artist.name must not be empty.")
    if not track.title.strip():
        raise ValidationError("CanonicalTrack.title must not be empty.")
    if track.duration_ms is not None and track.duration_ms < 0:
        raise ValidationError("CanonicalTrack.duration_ms must be non-negative.")


def validate_search_request(request: CanonicalSearchRequest) -> None:
    if not request.query.strip():
        raise ValidationError("CanonicalSearchRequest.query must not be empty.")
    if request.limit <= 0:
        raise ValidationError("CanonicalSearchRequest.limit must be positive.")
    if not request.country_code.strip():
        raise ValidationError("CanonicalSearchRequest.country_code must not be empty.")


def validate_playlist(playlist: CanonicalPlaylist) -> None:
    if not playlist.name.strip():
        raise ValidationError("CanonicalPlaylist.name must not be empty.")
    if not playlist.sections:
        raise ValidationError("CanonicalPlaylist.sections must not be empty.")
    for section in playlist.sections:
        if not section.name.strip():
            raise ValidationError("CanonicalPlaylistSection.name must not be empty.")
        for track in section.tracks:
            validate_track(track)
