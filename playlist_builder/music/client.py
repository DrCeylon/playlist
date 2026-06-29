from __future__ import annotations

from playlist_builder.core.applescript import apple_escape, run_applescript
from playlist_builder.core.models import TrackAddResult, TrackAddStatus, TrackRef
from playlist_builder.resolver.applescript import (
    build_candidate_collection_script,
    build_duplicate_batch_script,
)
from playlist_builder.resolver.constants import CANDIDATE_DELIMITER, FIELD_DELIMITER, RESULT_DELIMITER
from playlist_builder.resolver.models import ResolverCandidate
from playlist_builder.resolver.selection import select_best_candidate

BATCH_SIZE = 25


class MusicClient:
    def ensure_running(self) -> None:
        run_applescript('tell application "Music" to activate')

    def ensure_playlist(self, name: str) -> None:
        escaped = apple_escape(name)
        run_applescript(
            f'''
tell application "Music"
    if not (exists user playlist "{escaped}") then
        make new user playlist with properties {{name:"{escaped}"}}
    end if
end tell
'''
        )

    def clear_playlist_tracks(self, playlist_name: str) -> None:
        escaped = apple_escape(playlist_name)
        run_applescript(
            f'''
tell application "Music"
    if not (exists user playlist "{escaped}") then
        return
    end if
    set targetPlaylist to user playlist "{escaped}"
    repeat while (count of tracks of targetPlaylist) > 0
        delete track 1 of targetPlaylist
    end repeat
end tell
'''
        )

    def load_playlist_keys(self, playlist_name: str) -> set[str]:
        escaped = apple_escape(playlist_name)
        output = run_applescript(
            f'''
tell application "Music"
    set keyList to {{}}
    if not (exists user playlist "{escaped}") then
        return ""
    end if
    repeat with t in (tracks of user playlist "{escaped}")
        set end of keyList to ((artist of t) as text) & "::" & ((name of t) as text)
    end repeat
    set AppleScript's text item delimiters to "{RESULT_DELIMITER}"
    return keyList as text
end tell
'''
        )
        if not output:
            return set()
        return {self._normalize_key(part) for part in output.split(RESULT_DELIMITER) if part}

    def sync_playlist_order(
        self,
        playlist_name: str,
        tracks: list[TrackRef],
    ) -> list[TrackAddResult]:
        self.clear_playlist_tracks(playlist_name)
        return self.add_tracks(playlist_name, tracks, allow_duplicates=True)

    def add_tracks(
        self,
        playlist_name: str,
        tracks: list[TrackRef],
        *,
        existing_keys: set[str] | None = None,
        allow_duplicates: bool = False,
    ) -> list[TrackAddResult]:
        if not tracks:
            return []

        known_keys = existing_keys if existing_keys is not None else set()
        results: list[TrackAddResult | None] = [None] * len(tracks)
        pending: list[tuple[int, TrackRef]] = []

        for index, track in enumerate(tracks):
            if not allow_duplicates and track.key in known_keys:
                results[index] = TrackAddResult(track=track, status=TrackAddStatus.SKIPPED)
                continue
            pending.append((index, track))

        for offset in range(0, len(pending), BATCH_SIZE):
            batch = pending[offset : offset + BATCH_SIZE]
            indices, batch_tracks = zip(*batch, strict=True)
            batch_results = self._add_tracks_batch(playlist_name, list(batch_tracks))
            for index, result in zip(indices, batch_results, strict=True):
                if result.status == TrackAddStatus.ADDED:
                    known_keys.add(result.track.key)
                results[index] = result

        return [result for result in results if result is not None]

    def _add_tracks_batch(self, playlist_name: str, tracks: list[TrackRef]) -> list[TrackAddResult]:
        try:
            candidate_rows = self._collect_candidate_rows(tracks)
            decisions = [
                select_best_candidate(track, self._parse_candidates(track, row))
                for track, row in zip(tracks, candidate_rows, strict=True)
            ]
            selected_ids = [decision.selected.persistent_id for decision in decisions if decision.selected]
            duplicate_statuses = self._duplicate_selected_tracks(playlist_name, selected_ids)
        except RuntimeError as exc:
            return [
                TrackAddResult(track=track, status=TrackAddStatus.ERROR, error=str(exc))
                for track in tracks
            ]

        status_iter = iter(duplicate_statuses)
        batch_results: list[TrackAddResult] = []
        for decision in decisions:
            if not decision.selected:
                batch_results.append(TrackAddResult(track=decision.wanted, status=TrackAddStatus.NOT_FOUND))
                continue

            duplicate_status = next(status_iter, "not_found")
            if duplicate_status == "added":
                batch_results.append(TrackAddResult(track=decision.wanted, status=TrackAddStatus.ADDED))
            else:
                batch_results.append(TrackAddResult(track=decision.wanted, status=TrackAddStatus.NOT_FOUND))
        return batch_results

    def _collect_candidate_rows(self, tracks: list[TrackRef]) -> list[str]:
        output = run_applescript(build_candidate_collection_script(tracks))
        rows = output.split(RESULT_DELIMITER) if output else []
        if len(rows) != len(tracks):
            raise RuntimeError("Réponse AppleScript inattendue pendant la collecte des candidats.")
        return rows

    def _duplicate_selected_tracks(self, playlist_name: str, persistent_ids: list[str]) -> list[str]:
        if not persistent_ids:
            return []
        output = run_applescript(build_duplicate_batch_script(playlist_name, persistent_ids))
        statuses = output.split(RESULT_DELIMITER) if output else []
        if len(statuses) != len(persistent_ids):
            raise RuntimeError("Réponse AppleScript inattendue pendant l'ajout des morceaux.")
        return statuses

    @staticmethod
    def _parse_candidates(wanted: TrackRef, row: str) -> list[ResolverCandidate]:
        if not row:
            return []
        candidates: list[ResolverCandidate] = []
        for payload in row.split(CANDIDATE_DELIMITER):
            if not payload:
                continue
            artist, title, persistent_id, _query = MusicClient._parse_candidate_payload(payload)
            if artist and title and persistent_id:
                candidates.append(
                    ResolverCandidate(
                        wanted=wanted,
                        artist=artist,
                        title=title,
                        persistent_id=persistent_id,
                    )
                )
        return candidates

    @staticmethod
    def _parse_candidate_payload(payload: str) -> tuple[str, str, str, str]:
        parts = payload.split(FIELD_DELIMITER)
        padded = parts + [""] * (4 - len(parts))
        return padded[0], padded[1], padded[2], padded[3]

    @staticmethod
    def _normalize_key(value: str) -> str:
        artist, _, title = value.partition("::")
        return f"{artist.strip().lower()}::{title.strip().lower()}"
