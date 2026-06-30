from __future__ import annotations

import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterator

from playlist_builder.canonical.models import CanonicalCandidate
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.catalog_ids import catalog_url_from_candidate


class AppleMusicAcquisitionStatus(StrEnum):
    ADDED = "added"
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
        settle_delay_seconds: float = 1.5,
    ) -> None:
        self._applescript = applescript
        self._settle_delay_seconds = settle_delay_seconds

    def acquire_from_catalog_candidate(self, candidate: CanonicalCandidate) -> AppleMusicAcquisitionOutcome:
        url = catalog_url_from_candidate(candidate)
        if not url:
            return AppleMusicAcquisitionOutcome(AppleMusicAcquisitionStatus.ERROR, "URL catalogue indisponible.")

        status, detail = self._applescript.acquire_song_from_url(url)
        parsed_status = _parse_acquire_status(status)
        if parsed_status == AppleMusicAcquisitionStatus.ADDED:
            time.sleep(self._settle_delay_seconds)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.ADDED,
                detail or "Ajouté à la bibliothèque Music depuis le catalogue.",
            )
        if parsed_status == AppleMusicAcquisitionStatus.OPENED:
            time.sleep(self._settle_delay_seconds)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.OPENED,
                detail or "URL ouverte dans Music — clique sur + pour l'ajouter à ta bibliothèque.",
            )
        return AppleMusicAcquisitionOutcome(
            AppleMusicAcquisitionStatus.ERROR,
            detail or "Acquisition catalogue échouée.",
        )
