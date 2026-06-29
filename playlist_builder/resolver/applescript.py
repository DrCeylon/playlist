from __future__ import annotations

from playlist_builder.core.applescript import apple_escape
from playlist_builder.core.models import TrackRef
from playlist_builder.resolver.query import generate_query_variants

FIELD_DELIMITER = "\x1e"
RESULT_DELIMITER = "\x1f"


def build_resolve_batch_script(tracks: list[TrackRef]) -> str:
    """Build one AppleScript resolving many tracks with query variants.

    Each result row is encoded as: status, artist, title, score-like marker. The
    scoring is mostly performed by Apple Music search order here; Python can later
    add deeper validation if we expose all candidates.
    """

    blocks = []
    for track in tracks:
        variants = generate_query_variants(track)
        search_terms = ", ".join(f'"{apple_escape(variant.term)}"' for variant in variants)
        title = apple_escape(track.title)
        artist = apple_escape(track.artist)
        blocks.append(
            f'''
        set foundTrack to missing value
        set searchTerms to {{{search_terms}}}
        repeat with searchTerm in searchTerms
            if foundTrack is missing value then
                try
                    set searchResults to (search library playlist 1 for (searchTerm as text) only songs)
                    repeat with candidateTrack in searchResults
                        set candidateName to ((name of candidateTrack) as text)
                        set candidateArtist to ((artist of candidateTrack) as text)
                        if candidateName is "{title}" and candidateArtist is "{artist}" then
                            set foundTrack to candidateTrack
                            exit repeat
                        end if
                    end repeat
                    if foundTrack is missing value and (count of searchResults) > 0 then
                        set foundTrack to item 1 of searchResults
                    end if
                end try
            end if
        end repeat
        if foundTrack is missing value then
            set end of results to "not_found{FIELD_DELIMITER}{artist}{FIELD_DELIMITER}{title}{FIELD_DELIMITER}"
        else
            set resolvedArtist to ((artist of foundTrack) as text)
            set resolvedName to ((name of foundTrack) as text)
            duplicate foundTrack to targetPlaylist
            set end of results to "added{FIELD_DELIMITER}" & resolvedArtist & "{FIELD_DELIMITER}" & resolvedName & "{FIELD_DELIMITER}resolved"
        end if'''
        )

    return f'''
tell application "Music"
    set targetPlaylist to user playlist "{{playlist_name}}"
    set results to {{}}
{"".join(blocks)}
    set AppleScript's text item delimiters to "{RESULT_DELIMITER}"
    return results as text
end tell
'''
