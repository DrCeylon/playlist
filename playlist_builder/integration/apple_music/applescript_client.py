from __future__ import annotations

from playlist_builder.canonical.identity import track_identity_key
from playlist_builder.core.applescript import apple_escape, run_applescript
from playlist_builder.core.models import TrackRef
from playlist_builder.integration.apple_music.constants import (
    CANDIDATE_DELIMITER,
    FIELD_DELIMITER,
    MAX_CANDIDATES_PER_SEARCH,
    RESULT_DELIMITER,
)
from playlist_builder.integration.apple_music.models import AppleMusicTrack
from playlist_builder.resolver.query import generate_query_variants


class AppleScriptClient:
    """Low-level Apple Music.app adapter — no business logic."""

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

    def collect_candidates_batch(self, tracks: list[TrackRef]) -> list[list[AppleMusicTrack]]:
        if not tracks:
            return []
        script = self._build_collect_candidates_batch_script(tracks)
        try:
            output = run_applescript(script)
        except RuntimeError:
            return [[] for _ in tracks]

        rows = output.split(RESULT_DELIMITER) if output else []
        if len(rows) != len(tracks):
            return [[] for _ in tracks]
        return [self._parse_candidate_row(row) for row in rows]

    def add_tracks_by_persistent_id_batch(
        self,
        playlist_name: str,
        persistent_ids: list[str | None],
    ) -> list[str]:
        if not persistent_ids:
            return []
        escaped_playlist = apple_escape(playlist_name)
        script = self._build_add_by_persistent_id_batch_script(escaped_playlist, persistent_ids)
        try:
            output = run_applescript(script)
        except RuntimeError:
            return ["error"] * len(persistent_ids)

        rows = output.split(RESULT_DELIMITER) if output else []
        if len(rows) != len(persistent_ids):
            return ["error"] * len(persistent_ids)
        return rows

    @staticmethod
    def _normalize_key(value: str) -> str:
        artist, _, title = value.partition("::")
        return track_identity_key(artist, title)

    @staticmethod
    def _parse_candidate_row(row: str) -> list[AppleMusicTrack]:
        if not row:
            return []
        candidates: list[AppleMusicTrack] = []
        for chunk in row.split(CANDIDATE_DELIMITER):
            if not chunk:
                continue
            parts = chunk.split(FIELD_DELIMITER)
            if len(parts) < 4:
                continue
            persistent_id, artist, title, query = parts[0], parts[1], parts[2], parts[3]
            if not persistent_id.strip():
                continue
            candidates.append(
                AppleMusicTrack(
                    persistent_id=persistent_id.strip(),
                    artist=artist.strip(),
                    title=title.strip(),
                    query=query.strip(),
                )
            )
        return candidates

    @staticmethod
    def _build_collect_candidates_batch_script(tracks: list[TrackRef]) -> str:
        blocks: list[str] = []
        for track in tracks:
            variants = generate_query_variants(track)
            search_terms = ", ".join(f'"{apple_escape(variant.term)}"' for variant in variants)
            blocks.append(
                f'''
        set trackCandidates to {{}}
        set searchTerms to {{{search_terms}}}
        repeat with searchTerm in searchTerms
            try
                set searchResults to (search library playlist 1 for (searchTerm as text) only songs)
                set resultCount to count of searchResults
                set maxItems to {MAX_CANDIDATES_PER_SEARCH}
                if resultCount < maxItems then set maxItems to resultCount
                repeat with i from 1 to maxItems
                    set candidateTrack to item i of searchResults
                    set candidatePid to (persistent ID of candidateTrack) as text
                    set candidateArtist to ((artist of candidateTrack) as text)
                    set candidateName to ((name of candidateTrack) as text)
                    set end of trackCandidates to candidatePid & "{FIELD_DELIMITER}" & candidateArtist & "{FIELD_DELIMITER}" & candidateName & "{FIELD_DELIMITER}" & (searchTerm as text)
                end repeat
            end try
        end repeat
        set AppleScript's text item delimiters to "{CANDIDATE_DELIMITER}"
        set end of results to trackCandidates as text'''
            )

        return f'''
tell application "Music"
    set results to {{}}
{"".join(blocks)}
    set AppleScript's text item delimiters to "{RESULT_DELIMITER}"
    return results as text
end tell
'''

    @staticmethod
    def _build_add_by_persistent_id_batch_script(
        escaped_playlist: str,
        persistent_ids: list[str | None],
    ) -> str:
        blocks: list[str] = []
        for persistent_id in persistent_ids:
            if not persistent_id:
                blocks.append(f'        set end of results to "not_found{FIELD_DELIMITER}missing persistent id"')
                continue
            escaped_pid = apple_escape(persistent_id)
            blocks.append(
                f'''
        set foundTrack to missing value
        try
            set matches to (every track of library playlist 1 whose persistent ID is "{escaped_pid}")
            if (count of matches) > 0 then
                set foundTrack to item 1 of matches
            end if
        end try
        if foundTrack is missing value then
            set end of results to "not_found{FIELD_DELIMITER}{escaped_pid}"
        else
            duplicate foundTrack to targetPlaylist
            set end of results to "added{FIELD_DELIMITER}{escaped_pid}"
        end if'''
            )

        return f'''
tell application "Music"
    set targetPlaylist to user playlist "{escaped_playlist}"
    set results to {{}}
{"".join(blocks)}
    set AppleScript's text item delimiters to "{RESULT_DELIMITER}"
    return results as text
end tell
'''
