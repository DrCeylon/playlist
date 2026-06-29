from __future__ import annotations

from typing import Any


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
