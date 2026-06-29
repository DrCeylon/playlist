"""Backward-compatible planning constraint scoring facade.

New code should import from :mod:`playlist_builder.scoring`.
"""

from __future__ import annotations

from playlist_builder.scoring.constraint_engine import apply_text_preferences, is_rejected, rank_candidates
from playlist_builder.scoring.constants import EXCLUSION_PENALTY, INCLUSION_BOOST

__all__ = [
    "EXCLUSION_PENALTY",
    "INCLUSION_BOOST",
    "apply_text_preferences",
    "is_rejected",
    "rank_candidates",
]
