from __future__ import annotations

from playlist_builder.scoring.constants import MIN_ACCEPTABLE_SCORE

FIELD_DELIMITER = "\x1e"
RESULT_DELIMITER = "\x1f"
MAX_QUERY_VARIANTS = 6

_GENERIC_SECTIONS = frozenset({"playlist", "generated", "discovery"})

__all__ = [
    "FIELD_DELIMITER",
    "MAX_QUERY_VARIANTS",
    "MIN_ACCEPTABLE_SCORE",
    "RESULT_DELIMITER",
    "_GENERIC_SECTIONS",
]
