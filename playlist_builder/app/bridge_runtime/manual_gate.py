from __future__ import annotations

import threading
from dataclasses import dataclass

from playlist_builder.canonical.models import CanonicalCandidate, CanonicalTrack


@dataclass(frozen=True, slots=True)
class ManualAcquisitionInterrupted(Exception):
    """Raised when import must pause for a manual Music.app acquisition."""

    token: str
    instructions: str
    artist: str
    title: str
    catalog_label: str = ""


class ManualAcquisitionGate:
    """Coordinates manual acquisition pauses between bridge import and UI."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[str, threading.Event] = {}

    def wait(self, token: str) -> None:
        event = threading.Event()
        with self._lock:
            self._events[token] = event
        event.wait()
        with self._lock:
            self._events.pop(token, None)

    def continue_(self, token: str) -> bool:
        with self._lock:
            event = self._events.get(token)
        if event is None:
            return False
        event.set()
        return True

    def hook(
        self,
        track: CanonicalTrack,
        catalog_candidate: CanonicalCandidate,
        detail: str,
    ) -> None:
        artist = track.artist.display_name if track.artist else ""
        title = track.title
        catalog_label = catalog_candidate.track.label
        instructions = (
            "Acquisition manuelle requise dans Music.app.\n"
            f"{detail}\n"
            f"Correspondance catalogue : {catalog_label}\n"
            "Ajoute le morceau à ta bibliothèque, puis confirme dans Resonance."
        )
        token = track.identity_key
        raise ManualAcquisitionInterrupted(
            token=token,
            instructions=instructions,
            artist=artist,
            title=title,
            catalog_label=catalog_label,
        )
