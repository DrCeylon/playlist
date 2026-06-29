"""Backward-compatible resolver scoring facade.

New code should import from :mod:`playlist_builder.scoring`.
"""

from __future__ import annotations

from playlist_builder.scoring.match_engine import similarity_ratio, token_overlap
from playlist_builder.scoring.resolution import is_acceptable_match, score_resolution_match as score_candidate

__all__ = [
    "is_acceptable_match",
    "score_candidate",
    "similarity_ratio",
    "token_overlap",
]
