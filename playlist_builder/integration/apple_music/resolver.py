from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from playlist_builder.canonical.compat import legacy_track_from_canonical
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalTrack
from playlist_builder.core.models import TrackRef
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.mapper import resolution_candidates_from_apple_music_tracks
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


class AppleMusicResolver:
    """Resolves canonical tracks to Apple Music library persistent IDs."""

    def __init__(
        self,
        applescript: AppleScriptClient,
        identity_cache: IdentityCache,
        *,
        provider_id: ProviderId = ProviderId.APPLE_MUSIC,
    ) -> None:
        self._applescript = applescript
        self._identity_cache = identity_cache
        self._provider_id = provider_id

    def resolve(
        self,
        track: CanonicalTrack,
        *,
        section: str = "Playlist",
    ) -> AppleMusicResolutionOutcome:
        cached = self._identity_cache.get(track, self._provider_id)
        if cached is not None:
            return AppleMusicResolutionOutcome(
                track=track,
                persistent_id=cached.external_id,
                status=AppleMusicResolutionStatus.RESOLVED,
                cache_hit=True,
                score=cached.confidence,
            )

        legacy = legacy_track_from_canonical(track, section=section)
        try:
            candidate_groups = self._applescript.collect_candidates_batch([legacy])
        except RuntimeError as exc:
            return AppleMusicResolutionOutcome(
                track=track,
                persistent_id=None,
                status=AppleMusicResolutionStatus.ERROR,
                error=str(exc),
            )

        library_candidates = candidate_groups[0] if candidate_groups else []
        resolution_candidates = resolution_candidates_from_apple_music_tracks(library_candidates)
        decision = select_best_resolution(legacy, resolution_candidates)

        if decision.selected is None:
            return AppleMusicResolutionOutcome(
                track=track,
                persistent_id=None,
                status=AppleMusicResolutionStatus.NOT_FOUND,
                candidates=decision.candidates,
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
        )

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
                )
                continue
            pending.append((index, track, section))

        if not pending:
            return [outcome for outcome in outcomes if outcome is not None]

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
                )
            return [outcome for outcome in outcomes if outcome is not None]

        for (index, track, section), legacy, library_candidates in zip(
            pending, legacy_tracks, candidate_groups, strict=True
        ):
            del section
            resolution_candidates = resolution_candidates_from_apple_music_tracks(library_candidates)
            decision = select_best_resolution(legacy, resolution_candidates)

            if decision.selected is None:
                outcomes[index] = AppleMusicResolutionOutcome(
                    track=track,
                    persistent_id=None,
                    status=AppleMusicResolutionStatus.NOT_FOUND,
                    candidates=decision.candidates,
                )
                continue

            selected = decision.selected
            self._identity_cache.put_identity(
                track,
                provider_id=self._provider_id,
                external_id=selected.persistent_id,
                confidence=float(selected.score),
            )
            outcomes[index] = AppleMusicResolutionOutcome(
                track=track,
                persistent_id=selected.persistent_id,
                status=AppleMusicResolutionStatus.RESOLVED,
                cache_hit=False,
                score=float(selected.score),
                candidates=decision.candidates,
                selected_query=selected.query,
            )

        return [outcome for outcome in outcomes if outcome is not None]
