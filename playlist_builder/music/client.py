from __future__ import annotations

from playlist_builder.core.applescript import apple_escape, run_applescript
from playlist_builder.core.models import TrackAddResult, TrackAddStatus, TrackRef

RESULT_DELIMITER = "\x1f"
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
        results: list[TrackAddResult] = []
        pending: list[TrackRef] = []

        for track in tracks:
            if not allow_duplicates and track.key in known_keys:
                results.append(TrackAddResult(track=track, status=TrackAddStatus.SKIPPED))
                continue
            pending.append(track)

        for offset in range(0, len(pending), BATCH_SIZE):
            batch = pending[offset : offset + BATCH_SIZE]
            batch_results = self._add_tracks_batch(playlist_name, batch)
            for result in batch_results:
                if result.status == TrackAddStatus.ADDED:
                    known_keys.add(result.track.key)
                results.append(result)

        return results

    def _add_tracks_batch(self, playlist_name: str, tracks: list[TrackRef]) -> list[TrackAddResult]:
        escaped_playlist = apple_escape(playlist_name)
        blocks: list[str] = []
        for track in tracks:
            title = apple_escape(track.title)
            artist = apple_escape(track.artist)
            blocks.append(
                f'''
        try
            set foundTrack to first track of library playlist 1 whose name is "{title}" and artist is "{artist}"
            duplicate foundTrack to targetPlaylist
            set end of results to "added"
        on error
            try
                set foundTrack to first track of library playlist 1 whose name contains "{title}" and artist contains "{artist}"
                duplicate foundTrack to targetPlaylist
                set end of results to "added"
            on error
                set end of results to "not_found"
            end try
        end try'''
            )

        script = f'''
tell application "Music"
    set targetPlaylist to user playlist "{escaped_playlist}"
    set results to {{}}
{"".join(blocks)}
    set AppleScript's text item delimiters to "{RESULT_DELIMITER}"
    return results as text
end tell
'''
        try:
            output = run_applescript(script)
        except RuntimeError as exc:
            return [
                TrackAddResult(track=track, status=TrackAddStatus.ERROR, error=str(exc))
                for track in tracks
            ]

        statuses = output.split(RESULT_DELIMITER) if output else []
        if len(statuses) != len(tracks):
            return [
                TrackAddResult(
                    track=track,
                    status=TrackAddStatus.ERROR,
                    error="Réponse AppleScript inattendue.",
                )
                for track in tracks
            ]

        batch_results: list[TrackAddResult] = []
        for track, status in zip(tracks, statuses, strict=True):
            if status == "added":
                batch_results.append(TrackAddResult(track=track, status=TrackAddStatus.ADDED))
            else:
                batch_results.append(TrackAddResult(track=track, status=TrackAddStatus.NOT_FOUND))
        return batch_results

    @staticmethod
    def _normalize_key(value: str) -> str:
        artist, _, title = value.partition("::")
        return f"{artist.strip().lower()}::{title.strip().lower()}"
