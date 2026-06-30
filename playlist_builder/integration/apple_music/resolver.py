from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from playlist_builder.canonical.compat import legacy_track_from_canonical
from playlist_builder.canonical.contracts import CatalogSearchPort
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalTrack
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
            self._wait_until_user_added_track(track, acquisition.detail)

        refreshed = self._applescript.collect_candidates_batch([legacy])
        library_candidates = refreshed[0] if refreshed else []
        acquired = bool(library_candidates)
        if acquired:
            return library_candidates, True, acquisition.detail

        if acquisition.opened:
            return [], False, f"{acquisition.detail} Morceau toujours absent de la bibliothèque après confirmation."
        return [], False, acquisition.detail

    @staticmethod
    def _wait_until_user_added_track(track: CanonicalTrack, detail: str) -> None:
        artist = track.artist.name if track.artist else ""
        print(
            "\n📥 Acquisition manuelle requise "
            f"pour {artist} - {track.title}.\n"
            f"{detail}\n"
            "Ajoute le morceau à ta bibliothèque Music.app, puis appuie sur Entrée pour continuer...",
        )
        input()
