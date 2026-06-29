from __future__ import annotations

from typing import TYPE_CHECKING

from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalPlaylist,
    CanonicalPlaylistSection,
    CanonicalTrack,
)

if TYPE_CHECKING:
    from playlist_builder.core.models import PlaylistDefinition, TrackRef


def canonical_track_from_legacy(track: TrackRef) -> CanonicalTrack:
    """Map a legacy TrackRef to a canonical track (section metadata is excluded)."""

    return CanonicalTrack(
        artist=CanonicalArtist(name=track.artist.strip()),
        title=track.title.strip(),
    )


def legacy_track_from_canonical(
    track: CanonicalTrack,
    *,
    section: str = "Playlist",
) -> TrackRef:
    """Map a canonical track back to the legacy TrackRef used by current CLIs."""

    from playlist_builder.core.models import TrackRef

    return TrackRef(
        artist=track.artist.display_name,
        title=track.title.strip(),
        section=section.strip() or "Playlist",
    )


def canonical_playlist_from_legacy(playlist: PlaylistDefinition) -> CanonicalPlaylist:
    """Map a legacy playlist definition to the canonical playlist model."""

    return CanonicalPlaylist(
        name=playlist.name,
        description=playlist.description,
        sections=tuple(
            CanonicalPlaylistSection(
                name=section.name,
                tracks=tuple(canonical_track_from_legacy(track) for track in section.tracks),
            )
            for section in playlist.sections
        ),
    )


def legacy_tracks_from_canonical_playlist(playlist: CanonicalPlaylist) -> list[TrackRef]:
    """Flatten a canonical playlist into legacy TrackRef rows with section names."""

    from playlist_builder.core.models import TrackRef

    rows: list[TrackRef] = []
    for section in playlist.sections:
        for track in section.tracks:
            rows.append(
                TrackRef(
                    artist=track.artist.display_name,
                    title=track.title.strip(),
                    section=section.name,
                )
            )
    return rows
