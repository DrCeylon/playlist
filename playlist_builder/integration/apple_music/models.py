from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AppleMusicTrack:
    """Provider-specific Apple Music library track reference."""

    persistent_id: str
    artist: str
    title: str
    query: str = ""

    def validate(self) -> None:
        if not self.persistent_id.strip():
            raise ValueError("AppleMusicTrack.persistent_id must not be empty.")
        if not self.artist.strip() or not self.title.strip():
            raise ValueError("AppleMusicTrack artist and title must not be empty.")


class AppleITunesSearchHit:
    """Provider-specific iTunes Search API song payload."""

    __slots__ = ("raw",)

    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw

    @property
    def artist_name(self) -> str:
        return str(self.raw.get("artistName", ""))

    @property
    def track_name(self) -> str:
        return str(self.raw.get("trackName", ""))

    @property
    def track_view_url(self) -> str:
        return str(self.raw.get("trackViewUrl", ""))

    @property
    def track_id(self) -> str:
        value = self.raw.get("trackId")
        if value is None:
            return ""
        return str(value)

    @property
    def collection_name(self) -> str:
        return str(self.raw.get("collectionName", ""))

    @property
    def primary_genre_name(self) -> str:
        return str(self.raw.get("primaryGenreName", ""))

    @property
    def track_explicitness(self) -> str:
        return str(self.raw.get("trackExplicitness", ""))

    @property
    def is_explicit(self) -> bool:
        return self.track_explicitness == "explicit"

    @property
    def artwork_url(self) -> str:
        return str(self.raw.get("artworkUrl100", "") or self.raw.get("artworkUrl60", ""))

    @property
    def release_date(self) -> str:
        return str(self.raw.get("releaseDate", ""))

    @property
    def track_time_millis(self) -> int | None:
        value = self.raw.get("trackTimeMillis")
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @property
    def wrapper_type(self) -> str:
        return str(self.raw.get("wrapperType", ""))

    @property
    def kind(self) -> str:
        return str(self.raw.get("kind", ""))

    @property
    def artist_id(self) -> str:
        value = self.raw.get("artistId")
        if value is None:
            return ""
        return str(value)

    @property
    def collection_artist_id(self) -> str:
        value = self.raw.get("collectionArtistId")
        if value is None:
            return ""
        return str(value)

    @property
    def amg_artist_id(self) -> str:
        value = self.raw.get("amgArtistId")
        if value is None:
            return ""
        return str(value)
