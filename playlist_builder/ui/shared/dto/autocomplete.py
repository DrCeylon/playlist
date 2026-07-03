from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from playlist_builder.canonical.enums import ProviderId


class AutocompleteEntityKind(StrEnum):
    ARTIST = "artist"
    TRACK = "track"
    GENRE = "genre"
    KEYWORD = "keyword"


@dataclass(frozen=True, slots=True)
class AutocompleteContext:
    artist_name: str = ""
    artist_id: str = ""

    def to_dict(self) -> dict[str, str]:
        payload: dict[str, str] = {}
        if self.artist_name:
            payload["artist_name"] = self.artist_name
        if self.artist_id:
            payload["artist_id"] = self.artist_id
        return payload


@dataclass(frozen=True, slots=True)
class AutocompleteRequest:
    provider_id: ProviderId
    entity_kind: AutocompleteEntityKind
    query: str
    limit: int = 10
    context: AutocompleteContext | None = None


@dataclass(frozen=True, slots=True)
class ArtistSuggestion:
    id: str
    display_name: str
    sort_name: str = ""
    artwork_url: str = ""
    album_count: int | None = None
    artist_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "kind": AutocompleteEntityKind.ARTIST.value,
            "id": self.id,
            "display_name": self.display_name,
        }
        if self.sort_name:
            payload["sort_name"] = self.sort_name
        if self.artwork_url:
            payload["artwork_url"] = self.artwork_url
        if self.album_count is not None:
            payload["album_count"] = self.album_count
        if self.artist_type:
            payload["artist_type"] = self.artist_type
        return payload


@dataclass(frozen=True, slots=True)
class TrackSuggestion:
    id: str
    title: str
    artist_name: str
    album_title: str = ""
    release_year: int | None = None
    duration_ms: int | None = None
    artwork_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "kind": AutocompleteEntityKind.TRACK.value,
            "id": self.id,
            "title": self.title,
            "artist_name": self.artist_name,
        }
        if self.album_title:
            payload["album_title"] = self.album_title
        if self.release_year is not None:
            payload["release_year"] = self.release_year
        if self.duration_ms is not None:
            payload["duration_ms"] = self.duration_ms
        if self.artwork_url:
            payload["artwork_url"] = self.artwork_url
        return payload


@dataclass(frozen=True, slots=True)
class GenreSuggestion:
    id: str
    display_name: str
    synonyms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "kind": AutocompleteEntityKind.GENRE.value,
            "id": self.id,
            "display_name": self.display_name,
        }
        if self.synonyms:
            payload["synonyms"] = list(self.synonyms)
        return payload


@dataclass(frozen=True, slots=True)
class KeywordSuggestion:
    id: str
    label: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": AutocompleteEntityKind.KEYWORD.value,
            "id": self.id,
            "label": self.label,
        }


AutocompleteSuggestion = ArtistSuggestion | TrackSuggestion | GenreSuggestion | KeywordSuggestion


@dataclass(frozen=True, slots=True)
class AutocompleteResponse:
    suggestions: tuple[AutocompleteSuggestion, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"suggestions": [item.to_dict() for item in self.suggestions]}
