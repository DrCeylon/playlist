"""Backward-compatible catalog scoring facade.

New code should import from :mod:`playlist_builder.scoring`.
"""

from __future__ import annotations

from playlist_builder.scoring.constants import MIN_MATCH_SCORE, MIN_MUSICKIT_MATCH_SCORE
from playlist_builder.scoring.match_engine import pick_best_match, score_track_match
from playlist_builder.scoring.normalization import extract_catalog_artist_title as extract_artist_title

__all__ = [
    "MIN_MATCH_SCORE",
    "MIN_MUSICKIT_MATCH_SCORE",
    "extract_artist_title",
    "pick_best_match",
    "score_track_match",
]
