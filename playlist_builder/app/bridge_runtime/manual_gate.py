from __future__ import annotations

import threading

from playlist_builder.canonical.models import CanonicalCandidate, CanonicalTrack


class ManualAcquisitionInterrupted(Exception):
    """Raised when import must pause for a manual Music.app acquisition.

    Must remain a plain Exception subclass (not a frozen/slots dataclass) so
    context managers such as ``perf_span`` can attach tracebacks safely.
    """

    def __init__(
        self,
        *,
        token: str,
        instructions: str,
        artist: str,
        title: str,
        catalog_label: str = "",
        catalog_url: str = "",
        album: str = "",
    ) -> None:
        super().__init__(instructions)
        self.token = token
        self.instructions = instructions
        self.artist = artist
        self.title = title
        self.catalog_label = catalog_label
        self.catalog_url = catalog_url
        self.album = album


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
        album = catalog_candidate.track.album.title if catalog_candidate.track.album else ""
        catalog_url = _catalog_url_from_hints(catalog_candidate.provider_hints)
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
            catalog_url=catalog_url,
            album=album,
        )


def _catalog_url_from_hints(hints: tuple[str, ...]) -> str:
    for hint in hints:
        if hint.startswith("http") or hint.startswith("music://"):
            return hint.strip()
    return ""
