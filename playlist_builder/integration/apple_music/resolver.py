from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import time

from playlist_builder.canonical.compat import legacy_track_from_canonical
from playlist_builder.canonical.contracts import CatalogSearchPort
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalCandidate, CanonicalTrack
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.catalog_fallback import (
    catalog_lookup_for_track,
    enrich_resolution_message,
)
from playlist_builder.integration.apple_music.diagnostics import (
    AppleMusicResolutionTrace,
    trace_from_candidates,
)
from playlist_builder.integration.apple_music.library_acquisition import AppleMusicAcquisitionStatus, AppleMusicLibraryAcquisition
from playlist_builder.integration.apple_music.mapper import resolution_candidates_from_apple_music_tracks
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.resolver.query import generate_query_variants
from playlist_builder.scoring.resolution import ResolutionCandidate, select_best_resolution

_MANUAL_ACQUISITION_LIBRARY_ATTEMPTS = 4
_MANUAL_ACQUISITION_RETRY_DELAY_SECONDS = 5.0


class AppleMusicResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class AppleMusicResolutionOutcome:
    track: CanonicalTrack
    persistent_id: str | None
    status: AppleMusicResolutionStatus
    cache_hit: bool = False
    score: float = 0.0
    candidates: tuple[ResolutionCandidate, ...] = ()
    selected_query: str = ""
    error: str = ""
    trace: AppleMusicResolutionTrace = AppleMusicResolutionTrace()
    catalog_acquired: bool = False


class AppleMusicResolver:
    """Resolves canonical tracks to Apple Music library persistent IDs."""

    def __init__(
        self,
        applescript: AppleScriptClient,
        identity_cache: IdentityCache,
        *,
        provider_id: ProviderId = ProviderId.APPLE_MUSIC,
        catalog: CatalogSearchPort | None = None,
        country_code: str = "us",
        acquire_missing: bool = False,
        wait_for_manual_catalog_add: bool = True,
        catalog_acquisition_min_confidence: float = 70.0,
    ) -> None:
        self._applescript = applescript
        self._identity_cache = identity_cache
        self._provider_id = provider_id
        self._catalog = catalog
        self._country_code = country_code
        self._acquire_missing = acquire_missing
        self._wait_for_manual_catalog_add = wait_for_manual_catalog_add
        self._catalog_acquisition_min_confidence = catalog_acquisition_min_confidence
        self._acquisition = AppleMusicLibraryAcquisition(applescript)

    def resolve(
        self,
        track: CanonicalTrack,
        *,
        section: str = "Playlist",
    ) -> AppleMusicResolutionOutcome:
        return self.resolve_batch([(track, section)])[0]

    def resolve_batch(
        self,
        rows: list[tuple[CanonicalTrack, str]],
    ) -> list[AppleMusicResolutionOutcome]:
        outcomes: list[AppleMusicResolutionOutcome | None] = [None] * len(rows)
        pending: list[tuple[int, CanonicalTrack, str]] = []

        for index, (track, section) in enumerate(rows):
            cached = self._identity_cache.get(track, self._provider_id)
            if cached is not None:
                outcomes[index] = AppleMusicResolutionOutcome(
                    track=track,
                    persistent_id=cached.external_id,
                    status=AppleMusicResolutionStatus.RESOLVED,
                    cache_hit=True,
                    score=cached.confidence,
                    trace=AppleMusicResolutionTrace(cache_hit=True),
                )
                continue
            pending.append((index, track, section))

        if pending:
            self._resolve_pending(outcomes, pending)

        return [outcome for outcome in outcomes if outcome is not None]

    def _resolve_pending(
        self,
        outcomes: list[AppleMusicResolutionOutcome | None],
        pending: list[tuple[int, CanonicalTrack, str]],
    ) -> None:
        legacy_tracks = [
            legacy_track_from_canonical(track, section=section) for _, track, section in pending
        ]
        try:
            candidate_groups = self._applescript.collect_candidates_batch(legacy_tracks)
        except RuntimeError as exc:
            error = str(exc)
            for index, track, _section in pending:
                outcomes[index] = AppleMusicResolutionOutcome(
                    track=track,
                    persistent_id=None,
                    status=AppleMusicResolutionStatus.ERROR,
                    error=error,
                    trace=AppleMusicResolutionTrace(reason=error),
                )
            return

        for (index, track, section), legacy, library_candidates in zip(
            pending, legacy_tracks, candidate_groups, strict=True
        ):
            del section
            outcome = self._resolve_track(track, legacy, list(library_candidates))
            outcomes[index] = outcome

    def _resolve_track(
        self,
        track: CanonicalTrack,
        legacy,
        library_candidates: list[AppleMusicTrack],
    ) -> AppleMusicResolutionOutcome:
        catalog_acquired = False
        acquisition_note = ""

        if not library_candidates:
            library_candidates, catalog_acquired, acquisition_note = self._maybe_acquire_from_catalog(
                track,
                legacy,
            )

        resolution_candidates = resolution_candidates_from_apple_music_tracks(library_candidates)
        decision = select_best_resolution(legacy, resolution_candidates)
        expected_queries = tuple(variant.term for variant in generate_query_variants(legacy))
        trace = trace_from_candidates(
            candidates=decision.candidates,
            expected_queries=expected_queries,
            accepted=decision.selected,
            cache_hit=False,
            catalog_acquired=catalog_acquired,
            reason=acquisition_note,
        )

        if decision.selected is None:
            message = trace.summary()
            if acquisition_note:
                error = message
            else:
                error = enrich_resolution_message(
                    track,
                    message,
                    self._catalog,
                    country_code=self._country_code,
                )
            return AppleMusicResolutionOutcome(
                track=track,
                persistent_id=None,
                status=AppleMusicResolutionStatus.NOT_FOUND,
                candidates=decision.candidates,
                error=error,
                trace=trace,
                catalog_acquired=catalog_acquired,
            )

        selected = decision.selected
        self._identity_cache.put_identity(
            track,
            provider_id=self._provider_id,
            external_id=selected.persistent_id,
            confidence=float(selected.score),
        )
        return AppleMusicResolutionOutcome(
            track=track,
            persistent_id=selected.persistent_id,
            status=AppleMusicResolutionStatus.RESOLVED,
            cache_hit=False,
            score=float(selected.score),
            candidates=decision.candidates,
            selected_query=selected.query,
            trace=trace,
            catalog_acquired=catalog_acquired,
        )

    def _maybe_acquire_from_catalog(
        self,
        track: CanonicalTrack,
        legacy,
    ) -> tuple[list[AppleMusicTrack], bool, str]:
        if not self._acquire_missing or self._catalog is None:
            return [], False, ""

        catalog_candidate = catalog_lookup_for_track(
            track,
            self._catalog,
            country_code=self._country_code,
        )
        if catalog_candidate is None:
            return [], False, ""
        if catalog_candidate.raw_confidence < self._catalog_acquisition_min_confidence:
            return (
                [],
                False,
                (
                    f"Catalogue trouvé mais confiance insuffisante "
                    f"({catalog_candidate.raw_confidence:.0f} < {self._catalog_acquisition_min_confidence:.0f})."
                ),
            )

        acquisition = self._acquisition.acquire_from_catalog_candidate(catalog_candidate)
        if acquisition.status == AppleMusicAcquisitionStatus.ERROR:
            return [], False, acquisition.detail

        if acquisition.opened and self._wait_for_manual_catalog_add:
            self._wait_until_user_added_track(track, catalog_candidate, acquisition.detail)

        library_candidates = self._refresh_library_candidates_with_retries(
            legacy,
            catalog_candidate,
            after_manual_wait=acquisition.opened and self._wait_for_manual_catalog_add,
        )
        acquired = bool(library_candidates)
        if acquired:
            return library_candidates, True, acquisition.detail

        if acquisition.opened:
            return (
                [],
                False,
                (
                    f"{acquisition.detail} "
                    "Morceau toujours absent de la bibliothèque après confirmation "
                    f"({_MANUAL_ACQUISITION_LIBRARY_ATTEMPTS} recherches)."
                ),
            )
        return [], False, acquisition.detail

    def _refresh_library_candidates_with_retries(
        self,
        legacy,
        catalog_candidate: CanonicalCandidate,
        *,
        after_manual_wait: bool,
    ) -> list[AppleMusicTrack]:
        max_attempts = _MANUAL_ACQUISITION_LIBRARY_ATTEMPTS if after_manual_wait else 1
        for attempt in range(1, max_attempts + 1):
            if after_manual_wait:
                self._applescript.ensure_running()
            candidates = self._refresh_library_candidates(legacy, catalog_candidate)
            if candidates:
                if after_manual_wait and attempt > 1:
                    print(
                        f"✅ Morceau détecté en bibliothèque (tentative {attempt}/{max_attempts}).",
                        flush=True,
                    )
                return candidates
            if attempt < max_attempts and after_manual_wait:
                print(
                    f"⏳ Morceau pas encore visible en bibliothèque "
                    f"(tentative {attempt}/{max_attempts}) — "
                    f"nouvelle recherche dans {_MANUAL_ACQUISITION_RETRY_DELAY_SECONDS:.0f}s...",
                    flush=True,
                )
                time.sleep(_MANUAL_ACQUISITION_RETRY_DELAY_SECONDS)
        return []

    def _refresh_library_candidates(
        self,
        legacy,
        catalog_candidate: CanonicalCandidate,
    ) -> list[AppleMusicTrack]:
        section = getattr(legacy, "section", "Playlist") or "Playlist"
        search_rows = [legacy]
        catalog_legacy = legacy_track_from_canonical(catalog_candidate.track, section=section)
        if (
            catalog_legacy.artist.strip().casefold(),
            catalog_legacy.title.strip().casefold(),
        ) != (
            legacy.artist.strip().casefold(),
            legacy.title.strip().casefold(),
        ):
            search_rows.append(catalog_legacy)

        groups = self._applescript.collect_candidates_batch(search_rows)
        merged: list[AppleMusicTrack] = []
        seen: set[str] = set()
        for group in groups:
            for candidate in group:
                persistent_id = candidate.persistent_id.strip()
                if not persistent_id or persistent_id in seen:
                    continue
                seen.add(persistent_id)
                merged.append(candidate)
        return merged

    @staticmethod
    def _wait_until_user_added_track(
        track: CanonicalTrack,
        catalog_candidate: CanonicalCandidate,
        detail: str,
    ) -> None:
        artist = track.artist.name if track.artist else ""
        catalog_label = catalog_candidate.track.label
        print(
            "\n📥 Acquisition manuelle requise "
            f"pour {artist} - {track.title}.\n"
            f"{detail}\n"
            f"Correspondance catalogue : {catalog_label}\n"
            "Dans Music.app :\n"
            "  1. Clique sur « + » ou « Ajouter à la bibliothèque »\n"
            "  2. Vérifie que le morceau apparaît dans Bibliothèque\n"
            "  3. Reviens ici et appuie sur Entrée\n"
            "\n"
            "⚠️  N'appuie pas sur Entrée tant que le morceau n'est pas dans ta bibliothèque.",
            flush=True,
        )
        input()
