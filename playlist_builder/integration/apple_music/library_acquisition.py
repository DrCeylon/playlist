from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import time
from typing import Iterator

from playlist_builder.canonical.models import CanonicalCandidate
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient


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
        if not candidate.provider_hints:
            return AppleMusicAcquisitionOutcome(AppleMusicAcquisitionStatus.ERROR, "URL catalogue indisponible.")
        url = candidate.provider_hints[0].strip()
        if not url:
            return AppleMusicAcquisitionOutcome(AppleMusicAcquisitionStatus.ERROR, "URL catalogue vide.")

        status, detail = self._applescript.acquire_song_from_url(url)
        if status == AppleMusicAcquisitionStatus.ADDED:
            time.sleep(self._settle_delay_seconds)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.ADDED,
                detail or "Ajouté à la bibliothèque Music depuis le catalogue.",
            )
        if status == AppleMusicAcquisitionStatus.OPENED:
            time.sleep(self._settle_delay_seconds)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.OPENED,
                detail or "URL ouverte dans Music — ajout manuel requis.",
            )
        return AppleMusicAcquisitionOutcome(
            AppleMusicAcquisitionStatus.ERROR,
            detail or "Acquisition catalogue échouée.",
        )
