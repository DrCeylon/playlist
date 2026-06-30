from __future__ import annotations

import time

from playlist_builder.canonical.models import CanonicalCandidate
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient


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

    def acquire_from_catalog_candidate(self, candidate: CanonicalCandidate) -> tuple[bool, str]:
        if not candidate.provider_hints:
            return False, "URL catalogue indisponible."
        url = candidate.provider_hints[0].strip()
        if not url:
            return False, "URL catalogue vide."

        status, detail = self._applescript.acquire_song_from_url(url)
        if status == "added":
            time.sleep(self._settle_delay_seconds)
            return True, detail or "Ajouté à la bibliothèque Music depuis le catalogue."
        if status == "opened":
            time.sleep(self._settle_delay_seconds)
            return False, detail or "URL ouverte dans Music — ajout manuel requis."
        return False, detail or "Acquisition catalogue échouée."
