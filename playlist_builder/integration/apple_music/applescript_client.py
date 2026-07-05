from __future__ import annotations

import time

from playlist_builder.canonical.identity import track_identity_key
from playlist_builder.core.applescript import apple_escape, run_applescript
from playlist_builder.core.models import TrackRef
from playlist_builder.integration.apple_music.acquire_instrumentation import (
    ACQUIRE_POLL_DELAY_SECONDS,
    ACQUIRE_POLL_ITERATIONS,
    ACQUIRE_POST_PLAY_DELAY_SECONDS,
    acquire_song_from_url_with_tracing,
)
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

    def ensure_running(self, *, activate: bool = False) -> None:
        if activate:
            run_applescript('tell application "Music" to activate', operation="ensure_running_activate")
            return
        run_applescript(
            '''
tell application "Music"
    if it is not running then
        launch
    end if
end tell
''',
            operation="ensure_running",
        )

    def try_add_catalog_url(self, track_url: str) -> str:
        """Production S1 — quick `add URL` without open/play/duplicate (Phase 5.3.3)."""
        self.ensure_running(activate=False)
        return self._try_add_url(track_url)

    def open_catalog_url_for_manual(self, track_url: str, *, activate: bool = False) -> None:
        """Production S4 prep — open the catalog page so the user can add to Library."""
        self.ensure_running(activate=activate)
        self._open_catalog_url(track_url)

    def ensure_playlist(self, name: str) -> None:
        escaped = apple_escape(name)
        run_applescript(
            f'''
tell application "Music"
    if not (exists user playlist "{escaped}") then
        make new user playlist with properties {{name:"{escaped}"}}
    end if
end tell
''',
            operation="ensure_playlist",
        )

    def count_playlist_tracks(self, playlist_name: str) -> int:
        escaped = apple_escape(playlist_name)
        output = run_applescript(
            f'''
tell application "Music"
    if not (exists user playlist "{escaped}") then
        return "0"
    end if
    return (count of tracks of user playlist "{escaped}") as text
end tell
''',
            operation="count_playlist_tracks",
        )
        try:
            return max(0, int(output.strip()))
        except ValueError:
            return 0

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
''',
            operation="clear_playlist_tracks",
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
            output = run_applescript(script, operation="collect_candidates_batch")
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
            output = run_applescript(script, operation="add_tracks_by_persistent_id_batch")
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

    def acquire_song_from_url(
        self,
        url: str,
        *,
        artist: str = "",
        title: str = "",
        track_id: str = "",
        search_terms: list[str] | None = None,
        play_delay_seconds: float = 5.0,
        settle_delay_seconds: float = 6.0,
    ) -> tuple[str, str]:
        """Try to add a catalog track to the local Music library automatically.

        Strategy: ``add URL``, then play + duplicate current track to Library
        for subscription content, with optional ``music://`` / ``itms://`` URLs.

        Returns (status, detail) where status is one of:
        added, duplicated, opened, error.
        """
        return acquire_song_from_url_with_tracing(
            self,
            url,
            artist=artist,
            title=title,
            track_id=track_id,
            search_terms=search_terms,
            play_delay_seconds=play_delay_seconds,
            settle_delay_seconds=settle_delay_seconds,
        )

    def _acquire_song_from_url_monolithic(
        self,
        url: str,
        *,
        artist: str = "",
        title: str = "",
        track_id: str = "",
        search_terms: list[str] | None = None,
        play_delay_seconds: float = 5.0,
        settle_delay_seconds: float = 6.0,
    ) -> tuple[str, str]:
        urls_to_try = self._catalog_acquire_urls(url, track_id)
        if not urls_to_try:
            return "error", "URL catalogue indisponible."

        terms = list(search_terms or [])
        if not terms:
            terms = self._default_search_terms(artist, title)

        script = self._build_acquire_song_script(
            urls_to_try,
            search_terms=terms,
            play_delay_seconds=play_delay_seconds,
            settle_delay_seconds=settle_delay_seconds,
        )
        try:
            output = run_applescript(script, operation="acquire_song_from_url")
        except RuntimeError as exc:
            return "error", str(exc)

        return self._parse_acquire_output(output)

    def _acquire_song_from_url_phased(
        self,
        url: str,
        *,
        artist: str = "",
        title: str = "",
        track_id: str = "",
        search_terms: list[str] | None = None,
        play_delay_seconds: float = 5.0,
        settle_delay_seconds: float = 6.0,
    ) -> tuple[str, str]:
        """Investigation path: same logic as monolithic script, per-phase spans."""
        from playlist_builder.infrastructure.perf import perf_record, perf_span

        urls_to_try = self._catalog_acquire_urls(url, track_id)
        if not urls_to_try:
            return "error", "URL catalogue indisponible."

        terms = list(search_terms or [])
        if not terms:
            terms = self._default_search_terms(artist, title)

        perf_record(
            "acquire",
            "acquire_start",
            0,
            metadata={"url_count": len(urls_to_try), "search_term_count": len(terms)},
        )

        for index, track_url in enumerate(urls_to_try, start=1):
            with perf_span(
                "acquire",
                "add_url",
                metadata={"url_index": index, "url_scheme": track_url.split(":", 1)[0]},
            ):
                persistent_id = self._try_add_url(track_url)
            if persistent_id:
                perf_record("acquire", "acquire_success", 0, metadata={"path": "add_url", "url_index": index})
                return "added", persistent_id

        duplicate_attempted = False
        for index, track_url in enumerate(urls_to_try, start=1):
            with perf_span(
                "acquire",
                "open_location",
                metadata={"url_index": index, "url_scheme": track_url.split(":", 1)[0]},
            ):
                self._open_catalog_url(track_url)

            polls_used = 0
            with perf_span("acquire", "poll_current_track", metadata={"url_index": index}):
                polls_used = self._poll_for_current_track()
            perf_record(
                "acquire",
                "poll_current_track_result",
                0,
                metadata={"url_index": index, "polls_used": polls_used, "max_polls": ACQUIRE_POLL_ITERATIONS},
            )

            with perf_span(
                "acquire",
                "play_delay",
                metadata={"url_index": index, "seconds": play_delay_seconds},
            ):
                time.sleep(max(0.0, play_delay_seconds))

            with perf_span("acquire", "play", metadata={"url_index": index}):
                self._play_current_track()

            with perf_span(
                "acquire",
                "post_play_delay",
                metadata={"url_index": index, "seconds": ACQUIRE_POST_PLAY_DELAY_SECONDS},
            ):
                time.sleep(ACQUIRE_POST_PLAY_DELAY_SECONDS)

            with perf_span("acquire", "duplicate_to_library", metadata={"url_index": index}):
                self._duplicate_current_track_to_library()
                duplicate_attempted = True

            with perf_span(
                "acquire",
                "settle_delay",
                metadata={"url_index": index, "seconds": settle_delay_seconds},
            ):
                time.sleep(max(0.0, settle_delay_seconds))

            with perf_span("acquire", "library_search", metadata={"url_index": index, "term_count": len(terms)}):
                persistent_id = self._search_library_persistent_id(terms)
            if persistent_id:
                perf_record(
                    "acquire",
                    "acquire_success",
                    0,
                    metadata={"path": "open_duplicate_search", "url_index": index},
                )
                return "added", persistent_id

        if duplicate_attempted:
            perf_record("acquire", "acquire_success", 0, metadata={"path": "duplicated_fallback"})
            return "duplicated", "Duplication automatique vers la bibliothèque effectuée"

        with perf_span("acquire", "open_location_final", metadata={"url_index": 1}):
            try:
                self._open_catalog_url(urls_to_try[0])
            except RuntimeError as exc:
                return "error", str(exc)
        perf_record("acquire", "acquire_success", 0, metadata={"path": "opened_only"})
        return "opened", "URL ouverte dans Music — ajout automatique non confirmé"

    def _try_add_url(self, track_url: str) -> str:
        escaped = apple_escape(track_url)
        output = run_applescript(
            f'''
tell application "Music"
    try
        set addedItems to add "{escaped}"
        if (count of addedItems) > 0 then
            return (persistent ID of item 1 of addedItems) as text
        end if
    end try
    return ""
end tell
''',
            operation="acquire_add_url",
        )
        return output.strip()

    def _open_catalog_url(self, track_url: str) -> None:
        escaped = apple_escape(track_url)
        run_applescript(
            f'tell application "Music" to open location "{escaped}"',
            operation="acquire_open_location",
        )

    def _poll_for_current_track(self) -> int:
        polls_used = 0
        for attempt in range(1, ACQUIRE_POLL_ITERATIONS + 1):
            time.sleep(ACQUIRE_POLL_DELAY_SECONDS)
            polls_used = attempt
            if self._has_current_track():
                break
        return polls_used

    def _has_current_track(self) -> bool:
        output = run_applescript(
            '''
tell application "Music"
    try
        set _ to current track
        return "yes"
    on error
        return "no"
    end try
end tell
''',
            operation="acquire_probe_current_track",
        )
        return output.strip().casefold() == "yes"

    def _play_current_track(self) -> None:
        run_applescript('tell application "Music" to play', operation="acquire_play")

    def _duplicate_current_track_to_library(self) -> None:
        run_applescript(
            'tell application "Music" to duplicate current track to source "Library"',
            operation="acquire_duplicate_to_library",
        )

    def _search_library_persistent_id(self, search_terms: list[str]) -> str:
        for term in search_terms:
            normalized = term.strip()
            if not normalized:
                continue
            escaped = apple_escape(normalized)
            output = run_applescript(
                f'''
tell application "Music"
    set searchResults to (search library playlist 1 for "{escaped}" only songs)
    if (count of searchResults) > 0 then
        return (persistent ID of item 1 of searchResults) as text
    end if
    return ""
end tell
''',
                operation="acquire_library_search",
            )
            persistent_id = output.strip()
            if persistent_id:
                return persistent_id
        return ""

    @staticmethod
    def _parse_acquire_output(output: str) -> tuple[str, str]:
        if not output:
            return "error", "Réponse AppleScript vide."
        parts = output.split(FIELD_DELIMITER, 1)
        status = parts[0].strip()
        detail = parts[1].strip() if len(parts) > 1 else ""
        return status, detail

    @staticmethod
    def _default_search_terms(artist: str, title: str) -> list[str]:
        artist = artist.strip()
        title = title.strip()
        terms: list[str] = []
        if artist and title:
            terms.append(f"{artist} {title}")
        if title:
            terms.append(title)
        if artist:
            terms.append(artist)
        return terms

    @staticmethod
    def _catalog_acquire_urls(url: str, track_id: str) -> list[str]:
        urls: list[str] = []
        track_id = track_id.strip()
        if track_id:
            for candidate in (
                f"itms://music.apple.com/song/id{track_id}",
                f"https://music.apple.com/song/id{track_id}",
                f"music://music.apple.com/song/id{track_id}",
            ):
                if candidate not in urls:
                    urls.append(candidate)
        primary = url.strip()
        if primary and primary not in urls:
            urls.append(primary)
            if primary.startswith("https://music.apple.com/"):
                music_url = "music://" + primary[len("https://") :]
                if music_url not in urls:
                    urls.append(music_url)
        return urls

    @staticmethod
    def _build_acquire_song_script(
        urls: list[str],
        *,
        search_terms: list[str],
        play_delay_seconds: float,
        settle_delay_seconds: float,
    ) -> str:
        escaped_urls = ", ".join(f'"{apple_escape(item)}"' for item in urls)
        escaped_terms = ", ".join(f'"{apple_escape(term.strip())}"' for term in search_terms if term.strip())
        play_delay = max(0.0, play_delay_seconds)
        settle_delay = max(0.0, settle_delay_seconds)

        return f'''
tell application "Music"
    set urlsToTry to {{{escaped_urls}}}
    set searchTerms to {{{escaped_terms}}}
    repeat with trackUrl in urlsToTry
        try
            set addedItems to add (trackUrl as text)
            if (count of addedItems) > 0 then
                set addedTrack to item 1 of addedItems
                return "added{FIELD_DELIMITER}" & ((persistent ID of addedTrack) as text)
            end if
        end try
    end repeat

    set duplicateAttempted to false
    repeat with trackUrl in urlsToTry
        try
            open location (trackUrl as text)
            repeat with i from 1 to 16
                delay 0.5
                try
                    set currentTrackRef to current track
                    exit repeat
                end try
            end repeat
            delay {play_delay}
            try
                play
            end try
            delay 1
            duplicate current track to source "Library"
            set duplicateAttempted to true
            delay {settle_delay}
            repeat with searchTerm in searchTerms
                if (searchTerm as text) is not "" then
                    set searchResults to (search library playlist 1 for (searchTerm as text) only songs)
                    if (count of searchResults) > 0 then
                        set foundTrack to item 1 of searchResults
                        return "added{FIELD_DELIMITER}" & ((persistent ID of foundTrack) as text)
                    end if
                end if
            end repeat
        end try
    end repeat

    if duplicateAttempted then
        return "duplicated{FIELD_DELIMITER}Duplication automatique vers la bibliothèque effectuée"
    end if
    try
        open location (item 1 of urlsToTry as text)
        return "opened{FIELD_DELIMITER}URL ouverte dans Music — ajout automatique non confirmé"
    on error errMsg
        return "error{FIELD_DELIMITER}" & errMsg
    end try
end tell
'''

