from __future__ import annotations

from playlist_builder.canonical.identity import track_identity_key
from playlist_builder.core.applescript import apple_escape, run_applescript
from playlist_builder.core.models import TrackAddResult, TrackAddStatus, TrackRef
from playlist_builder.resolver.applescript import (
    FIELD_DELIMITER,
    RESULT_DELIMITER,
    build_resolve_batch_script,
)

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
        escaped_playlist = apple_escape(playlist_name)
        script = build_resolve_batch_script(tracks).replace("{playlist_name}", escaped_playlist)

        try:
            output = run_applescript(script)
        except RuntimeError as exc:
            return [
                TrackAddResult(track=track, status=TrackAddStatus.ERROR, error=str(exc))
                for track in tracks
            ]

        rows = output.split(RESULT_DELIMITER) if output else []
        if len(rows) != len(tracks):
            return [
                TrackAddResult(
                    track=track,
                    status=TrackAddStatus.ERROR,
                    error="Réponse AppleScript inattendue.",
                )
                for track in tracks
            ]

        batch_results: list[TrackAddResult] = []
        for track, row in zip(tracks, rows, strict=True):
            status, _, _resolved_title, detail = self._parse_result_row(row)
            if status == "added":
                batch_results.append(TrackAddResult(track=track, status=TrackAddStatus.ADDED))
            elif status == "not_found":
                batch_results.append(TrackAddResult(track=track, status=TrackAddStatus.NOT_FOUND))
            else:
                batch_results.append(
                    TrackAddResult(
                        track=track,
                        status=TrackAddStatus.ERROR,
                        error=detail or "Statut AppleScript inconnu.",
                    )
                )
        return batch_results

    @staticmethod
    def _parse_result_row(row: str) -> tuple[str, str, str, str]:
        parts = row.split(FIELD_DELIMITER)
        padded = parts + [""] * (4 - len(parts))
        return padded[0], padded[1], padded[2], padded[3]

    @staticmethod
    def _normalize_key(value: str) -> str:
        artist, _, title = value.partition("::")
        return track_identity_key(artist, title)
