from __future__ import annotations

from playlist_builder.core.applescript import apple_escape
from playlist_builder.core.models import TrackRef
from playlist_builder.resolver.constants import (
    CANDIDATE_DELIMITER,
    FIELD_DELIMITER,
    MAX_CANDIDATES_PER_TRACK,
    RESULT_DELIMITER,
)
from playlist_builder.resolver.query import generate_query_variants


def build_candidate_collection_script(tracks: list[TrackRef]) -> str:
    """Build one AppleScript that returns multiple candidates per track.

    Python performs the final scoring and selection. AppleScript only gathers
    candidates efficiently through Music's native search.
    """

    blocks = []
    for track_index, track in enumerate(tracks):
        variants = generate_query_variants(track)
        search_terms = ", ".join(f'"{apple_escape(variant.term)}"' for variant in variants)
        blocks.append(
            f'''
        set candidateRows to {{}}
        set searchTerms to {{{search_terms}}}
        repeat with searchTerm in searchTerms
            if (count of candidateRows) < {MAX_CANDIDATES_PER_TRACK} then
                try
                    set searchResults to (search library playlist 1 for (searchTerm as text) only songs)
                    repeat with candidateTrack in searchResults
                        if (count of candidateRows) < {MAX_CANDIDATES_PER_TRACK} then
                            set candidateName to ((name of candidateTrack) as text)
                            set candidateArtist to ((artist of candidateTrack) as text)
                            set candidateId to ((persistent ID of candidateTrack) as text)
                            set end of candidateRows to candidateArtist & "{FIELD_DELIMITER}" & candidateName & "{FIELD_DELIMITER}" & candidateId & "{FIELD_DELIMITER}" & (searchTerm as text)
                        end if
                    end repeat
                end try
            end if
        end repeat
        set AppleScript's text item delimiters to "{CANDIDATE_DELIMITER}"
        set end of results to (candidateRows as text)'''
        )

    return f'''
tell application "Music"
    set results to {{}}
{"".join(blocks)}
    set AppleScript's text item delimiters to "{RESULT_DELIMITER}"
    return results as text
end tell
'''


def build_duplicate_batch_script(playlist_name: str, persistent_ids: list[str]) -> str:
    escaped_playlist = apple_escape(playlist_name)
    blocks = []
    for persistent_id in persistent_ids:
        escaped_id = apple_escape(persistent_id)
        blocks.append(
            f'''
        try
            set foundTrack to first track of library playlist 1 whose persistent ID is "{escaped_id}"
            duplicate foundTrack to targetPlaylist
            set end of results to "added"
        on error
            set end of results to "not_found"
        end try'''
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


# Backward-compatible alias for tests/imports that still reference the old name.
def build_resolve_batch_script(tracks: list[TrackRef]) -> str:
    return build_candidate_collection_script(tracks)
