from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TrackRef:
    artist: str
    title: str
    section: str = "Playlist"

    @property
    def key(self) -> str:
        return f"{self.artist.strip().lower()}::{self.title.strip().lower()}"

    @property
    def label(self) -> str:
        return f"{self.artist} - {self.title}"


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
