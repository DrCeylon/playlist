from __future__ import annotations

import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterator

from playlist_builder.canonical.models import CanonicalCandidate
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.catalog_ids import (
    catalog_track_id_from_candidate,
    catalog_url_from_candidate,
)


class AppleMusicAcquisitionStatus(StrEnum):
    ADDED = "added"
    DUPLICATED = "duplicated"
    OPENED = "opened"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class AppleMusicAcquisitionOutcome:
    status: AppleMusicAcquisitionStatus
    detail: str

    @property
    def added(self) -> bool:
        return self.status == AppleMusicAcquisitionStatus.ADDED

    @property
    def opened(self) -> bool:
        return self.status == AppleMusicAcquisitionStatus.OPENED

    @property
    def duplicated(self) -> bool:
        return self.status == AppleMusicAcquisitionStatus.DUPLICATED

    @property
    def automatic_attempted(self) -> bool:
        return self.status in {
            AppleMusicAcquisitionStatus.ADDED,
            AppleMusicAcquisitionStatus.DUPLICATED,
            AppleMusicAcquisitionStatus.OPENED,
        }

    def __iter__(self) -> Iterator[bool | str]:
        """Allow old tests/callers to unpack `(added, detail)` during migration."""
        yield self.added
        yield self.detail


def _parse_acquire_status(status: str) -> AppleMusicAcquisitionStatus:
    normalized = status.strip().lower()
    try:
        return AppleMusicAcquisitionStatus(normalized)
    except ValueError:
        return AppleMusicAcquisitionStatus.ERROR


class AppleMusicLibraryAcquisition:
    """Acquires catalog tracks into the local Music.app library before resolution."""

    def __init__(
        self,
        applescript: AppleScriptClient,
        *,
        settle_delay_seconds: float = 6.0,
        play_delay_seconds: float = 5.0,
    ) -> None:
        self._applescript = applescript
        self._settle_delay_seconds = settle_delay_seconds
        self._play_delay_seconds = play_delay_seconds

    def acquire_from_catalog_candidate(self, candidate: CanonicalCandidate) -> AppleMusicAcquisitionOutcome:
        url = catalog_url_from_candidate(candidate)
        if not url:
            return AppleMusicAcquisitionOutcome(AppleMusicAcquisitionStatus.ERROR, "URL catalogue indisponible.")

        artist = candidate.track.artist.name
        title = candidate.track.title
        track_id = catalog_track_id_from_candidate(candidate)
        search_terms = _catalog_search_terms(artist, title)

        status, detail = self._applescript.acquire_song_from_url(
            url,
            artist=artist,
            title=title,
            track_id=track_id,
            search_terms=search_terms,
            play_delay_seconds=self._play_delay_seconds,
            settle_delay_seconds=self._settle_delay_seconds,
        )
        parsed_status = _parse_acquire_status(status)
        if parsed_status == AppleMusicAcquisitionStatus.ADDED:
            time.sleep(self._settle_delay_seconds)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.ADDED,
                detail or "Ajouté à la bibliothèque Music depuis le catalogue.",
            )
        if parsed_status == AppleMusicAcquisitionStatus.DUPLICATED:
            time.sleep(self._settle_delay_seconds)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.DUPLICATED,
                detail or "Duplication automatique vers la bibliothèque effectuée.",
            )
        if parsed_status == AppleMusicAcquisitionStatus.OPENED:
            time.sleep(self._settle_delay_seconds)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.OPENED,
                detail or "URL ouverte dans Music — ajout automatique non confirmé.",
            )
        return AppleMusicAcquisitionOutcome(
            AppleMusicAcquisitionStatus.ERROR,
            detail or "Acquisition catalogue échouée.",
        )


def _catalog_search_terms(artist: str, title: str) -> list[str]:
    artist = artist.strip()
    title = title.strip()
    terms: list[str] = []
    if artist and title:
        terms.append(f"{artist} {title}")
    if title:
        terms.append(title)
    if artist:
        terms.append(artist)
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        key = term.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(term)
    return unique
