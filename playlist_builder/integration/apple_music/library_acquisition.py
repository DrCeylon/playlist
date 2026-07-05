from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterator

from playlist_builder.canonical.models import CanonicalCandidate
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.acquire_instrumentation import record_post_acquisition_settle
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
        acquisition_mode: str = "",
    ) -> None:
        self._applescript = applescript
        self._settle_delay_seconds = settle_delay_seconds
        self._play_delay_seconds = play_delay_seconds
        from playlist_builder.integration.apple_music.acquisition_policy import (
            CatalogAcquisitionMode,
            ENABLE_PLAY_DUPLICATE_ACQUISITION_DEFAULT,
        )

        if acquisition_mode:
            self._acquisition_mode = CatalogAcquisitionMode(acquisition_mode)
        elif ENABLE_PLAY_DUPLICATE_ACQUISITION_DEFAULT:
            self._acquisition_mode = CatalogAcquisitionMode.LEGACY_EXPERIMENTAL
        else:
            self._acquisition_mode = CatalogAcquisitionMode.PRODUCTION

    def acquire_from_catalog_candidate(self, candidate: CanonicalCandidate) -> AppleMusicAcquisitionOutcome:
        from playlist_builder.integration.apple_music.acquisition_policy import CatalogAcquisitionMode

        if self._acquisition_mode == CatalogAcquisitionMode.LEGACY_EXPERIMENTAL:
            return self._acquire_legacy_experimental(candidate)
        return self._acquire_production(candidate)

    def _acquire_production(self, candidate: CanonicalCandidate) -> AppleMusicAcquisitionOutcome:
        url = catalog_url_from_candidate(candidate)
        track_id = catalog_track_id_from_candidate(candidate)
        if not url and not track_id:
            return AppleMusicAcquisitionOutcome(AppleMusicAcquisitionStatus.ERROR, "URL catalogue indisponible.")

        artist = candidate.track.artist.name
        title = candidate.track.title

        print(
            f"🔎 Acquisition catalogue : {artist} - {title} — vérification rapide add URL…",
            flush=True,
        )

        persistent_id = self._try_quick_add_urls(url=url, track_id=track_id)
        if persistent_id:
            record_post_acquisition_settle(1.0, status=AppleMusicAcquisitionStatus.ADDED.value)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.ADDED,
                persistent_id,
            )

        open_url = self._preferred_open_url(url=url, track_id=track_id)
        if not open_url:
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.ERROR,
                "URL catalogue indisponible pour ouvrir Music.app.",
            )

        try:
            self._applescript.open_catalog_url_for_manual(open_url, activate=False)
        except RuntimeError as exc:
            return AppleMusicAcquisitionOutcome(AppleMusicAcquisitionStatus.ERROR, str(exc))

        return AppleMusicAcquisitionOutcome(
            AppleMusicAcquisitionStatus.OPENED,
            (
                "Le morceau n'est pas encore dans votre bibliothèque Music.app. "
                "La fiche catalogue a été ouverte — ajoutez-le à votre bibliothèque, "
                "puis confirmez dans Resonance."
            ),
        )

    def _acquire_legacy_experimental(self, candidate: CanonicalCandidate) -> AppleMusicAcquisitionOutcome:
        url = catalog_url_from_candidate(candidate)
        if not url:
            return AppleMusicAcquisitionOutcome(AppleMusicAcquisitionStatus.ERROR, "URL catalogue indisponible.")

        artist = candidate.track.artist.name
        title = candidate.track.title
        track_id = catalog_track_id_from_candidate(candidate)
        search_terms = _catalog_search_terms(artist, title)

        print(
            f"🤖 Ajout automatique dans Music.app : {artist} - {title}...",
            flush=True,
        )
        print("   (peut prendre 20–30 secondes, Music.app doit rester accessible)", flush=True)

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
            record_post_acquisition_settle(self._settle_delay_seconds, status=parsed_status.value)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.ADDED,
                detail or "Ajouté à la bibliothèque Music depuis le catalogue.",
            )
        if parsed_status == AppleMusicAcquisitionStatus.DUPLICATED:
            record_post_acquisition_settle(self._settle_delay_seconds, status=parsed_status.value)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.DUPLICATED,
                detail or "Duplication automatique vers la bibliothèque effectuée.",
            )
        if parsed_status == AppleMusicAcquisitionStatus.OPENED:
            record_post_acquisition_settle(self._settle_delay_seconds, status=parsed_status.value)
            return AppleMusicAcquisitionOutcome(
                AppleMusicAcquisitionStatus.OPENED,
                detail or "URL ouverte dans Music — ajout automatique non confirmé.",
            )
        return AppleMusicAcquisitionOutcome(
            AppleMusicAcquisitionStatus.ERROR,
            detail or "Acquisition catalogue échouée.",
        )

    def _try_quick_add_urls(self, *, url: str, track_id: str) -> str:
        candidates: list[str] = []
        if track_id:
            candidates.append(f"itms://music.apple.com/song/id{track_id}")
        if url.strip() and url not in candidates:
            candidates.append(url.strip())
        for candidate_url in candidates:
            persistent_id = self._applescript.try_add_catalog_url(candidate_url)
            if persistent_id:
                return persistent_id
        return ""

    @staticmethod
    def _preferred_open_url(*, url: str, track_id: str) -> str:
        if url.strip():
            return url.strip()
        if track_id.strip():
            return f"https://music.apple.com/song/id{track_id.strip()}"
        return ""


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
