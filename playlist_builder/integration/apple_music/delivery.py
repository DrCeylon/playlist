from __future__ import annotations

import time

from playlist_builder.canonical.enums import ImportStatus
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalImportResult, CanonicalPlaylist
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.constants import FIELD_DELIMITER
from playlist_builder.integration.apple_music.delivery_pacing import (
    DELIVERY_ADD_RETRY_POLICY,
    pace_between_delivery_batches,
    retry_delay_for_attempt,
    wait_for_playlist_cleared,
    wait_for_playlist_track_count,
)
from playlist_builder.integration.apple_music.resolver import (
    AppleMusicResolutionOutcome,
    AppleMusicResolutionStatus,
)

BATCH_SIZE = 25


class AppleMusicDelivery:
    """Materializes resolved tracks into an Apple Music user playlist."""

    def __init__(self, applescript: AppleScriptClient) -> None:
        self._applescript = applescript

    def ensure_playlist(self, name: str) -> None:
        self._applescript.ensure_running()
        self._applescript.ensure_playlist(name)

    def add_resolved_track(
        self,
        playlist_name: str,
        outcome: AppleMusicResolutionOutcome,
        *,
        section_name: str,
        existing_keys: set[str] | None = None,
    ) -> CanonicalImportResult:
        known_keys = set(existing_keys or ())
        if outcome.status != AppleMusicResolutionStatus.RESOLVED:
            return _result_from_outcome(outcome, section_name)
        track_key = outcome.track.identity_key
        if track_key in known_keys:
            return CanonicalImportResult(
                track=outcome.track,
                status=ImportStatus.SKIPPED,
                section_name=section_name,
            )
        statuses = self._add_batch_with_retry(playlist_name, [(0, outcome, section_name)])
        status = statuses[0]
        if status.startswith("added"):
            return CanonicalImportResult(
                track=outcome.track,
                status=ImportStatus.ADDED,
                section_name=section_name,
            )
        if status.startswith("not_found"):
            return CanonicalImportResult(
                track=outcome.track,
                status=ImportStatus.NOT_FOUND,
                section_name=section_name,
                error="Apple Music library track introuvable pour le persistent ID résolu.",
            )
        _, _, detail = _parse_delivery_status(status)
        return CanonicalImportResult(
            track=outcome.track,
            status=ImportStatus.ERROR,
            section_name=section_name,
            error=detail or "Erreur AppleScript lors de l'ajout.",
        )

    def sync_playlist(
        self,
        playlist: CanonicalPlaylist,
        outcomes: list[AppleMusicResolutionOutcome],
    ) -> CanonicalImportReport:
        resolved = [outcome for outcome in outcomes if outcome.status == AppleMusicResolutionStatus.RESOLVED]
        if not resolved:
            return self._import_resolved_tracks(playlist, outcomes, existing_keys=None, allow_duplicates=True)
        self._clear_playlist_with_confirmation(playlist.name)
        report = self._import_resolved_tracks(playlist, outcomes, existing_keys=None, allow_duplicates=True)
        added_count = sum(1 for item in report.results if item.status == ImportStatus.ADDED)
        if added_count > 0:
            wait_for_playlist_track_count(
                self._applescript,
                playlist.name,
                minimum_count=added_count,
            )
        return report

    def import_incremental(
        self,
        playlist: CanonicalPlaylist,
        outcomes: list[AppleMusicResolutionOutcome],
        *,
        existing_keys: set[str] | None = None,
        allow_duplicates: bool = False,
    ) -> CanonicalImportReport:
        return self._import_resolved_tracks(
            playlist,
            outcomes,
            existing_keys=existing_keys,
            allow_duplicates=allow_duplicates,
        )

    def _clear_playlist_with_confirmation(self, playlist_name: str) -> None:
        self._applescript.clear_playlist_tracks(playlist_name)
        wait_for_playlist_cleared(self._applescript, playlist_name)

    def _import_resolved_tracks(
        self,
        playlist: CanonicalPlaylist,
        outcomes: list[AppleMusicResolutionOutcome],
        *,
        existing_keys: set[str] | None,
        allow_duplicates: bool,
    ) -> CanonicalImportReport:
        rows = _flatten_playlist_with_outcomes(playlist, outcomes)
        known_keys = set(existing_keys or ())
        results: list[CanonicalImportResult | None] = [None] * len(rows)
        pending: list[tuple[int, AppleMusicResolutionOutcome, str]] = []

        for index, (outcome, section_name) in enumerate(rows):
            if outcome.status != AppleMusicResolutionStatus.RESOLVED:
                results[index] = _result_from_outcome(outcome, section_name)
                continue

            track_key = outcome.track.identity_key
            if not allow_duplicates and track_key in known_keys:
                results[index] = CanonicalImportResult(
                    track=outcome.track,
                    status=ImportStatus.SKIPPED,
                    section_name=section_name,
                )
                continue
            pending.append((index, outcome, section_name))

        batch_index = 0
        for offset in range(0, len(pending), BATCH_SIZE):
            pace_between_delivery_batches(batch_index)
            batch_index += 1
            batch = pending[offset : offset + BATCH_SIZE]
            statuses = self._add_batch_with_retry(playlist.name, batch)
            for (index, outcome, section_name), status in zip(batch, statuses, strict=True):
                if status.startswith("added"):
                    known_keys.add(outcome.track.identity_key)
                    results[index] = CanonicalImportResult(
                        track=outcome.track,
                        status=ImportStatus.ADDED,
                        section_name=section_name,
                    )
                elif status.startswith("not_found"):
                    results[index] = CanonicalImportResult(
                        track=outcome.track,
                        status=ImportStatus.NOT_FOUND,
                        section_name=section_name,
                        error="Apple Music library track introuvable pour le persistent ID résolu.",
                    )
                else:
                    _, _, detail = _parse_delivery_status(status)
                    results[index] = CanonicalImportResult(
                        track=outcome.track,
                        status=ImportStatus.ERROR,
                        section_name=section_name,
                        error=detail or "Erreur AppleScript lors de l'ajout.",
                    )

        return CanonicalImportReport(
            playlist_name=playlist.name,
            results=tuple(result for result in results if result is not None),
        )

    def _add_batch_with_retry(
        self,
        playlist_name: str,
        batch: list[tuple[int, AppleMusicResolutionOutcome, str]],
    ) -> list[str]:
        persistent_ids = [item[1].persistent_id for item in batch]
        statuses = self._applescript.add_tracks_by_persistent_id_batch(playlist_name, persistent_ids)
        total_wait = 0.0
        for attempt in range(2, DELIVERY_ADD_RETRY_POLICY.max_attempts + 1):
            retry_indexes = [
                index
                for index, status in enumerate(statuses)
                if status.startswith("not_found") or status.startswith("error")
            ]
            if not retry_indexes:
                break
            delay = retry_delay_for_attempt(attempt - 1)
            if total_wait + delay > DELIVERY_ADD_RETRY_POLICY.max_total_wait:
                break
            time.sleep(delay)
            total_wait += delay
            retry_ids = [persistent_ids[index] for index in retry_indexes]
            retry_statuses = self._applescript.add_tracks_by_persistent_id_batch(playlist_name, retry_ids)
            for batch_index, status in zip(retry_indexes, retry_statuses, strict=True):
                statuses[batch_index] = status
        return statuses


def _flatten_playlist_with_outcomes(
    playlist: CanonicalPlaylist,
    outcomes: list[AppleMusicResolutionOutcome],
) -> list[tuple[AppleMusicResolutionOutcome, str]]:
    flat_sections: list[str] = []
    for section in playlist.sections:
        for _track in section.tracks:
            flat_sections.append(section.name)

    if len(flat_sections) != len(outcomes):
        raise ValueError("Resolution outcomes do not match playlist track count.")

    return list(zip(outcomes, flat_sections, strict=True))


def _result_from_outcome(outcome: AppleMusicResolutionOutcome, section_name: str) -> CanonicalImportResult:
    if outcome.status == AppleMusicResolutionStatus.ERROR:
        return CanonicalImportResult(
            track=outcome.track,
            status=ImportStatus.ERROR,
            section_name=section_name,
            error=outcome.error or "Erreur de résolution.",
        )
    return CanonicalImportResult(
        track=outcome.track,
        status=ImportStatus.NOT_FOUND,
        section_name=section_name,
        error=outcome.error or "Aucun candidat acceptable dans la bibliothèque Apple Music.",
    )


def _parse_delivery_status(status: str) -> tuple[str, str, str]:
    parts = status.split(FIELD_DELIMITER, 1)
    if len(parts) == 1:
        return parts[0], "", ""
    return parts[0], parts[1], parts[1]
