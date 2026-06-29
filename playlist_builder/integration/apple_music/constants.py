from __future__ import annotations

from playlist_builder.resolver.constants import (
    FIELD_DELIMITER,
    MAX_QUERY_VARIANTS,
    MIN_ACCEPTABLE_SCORE,
    RESULT_DELIMITER,
)

CANDIDATE_DELIMITER = "\x1d"
MAX_CANDIDATES_PER_SEARCH = 5

__all__ = [
    "CANDIDATE_DELIMITER",
    "FIELD_DELIMITER",
    "MAX_CANDIDATES_PER_SEARCH",
    "MAX_QUERY_VARIANTS",
    "MIN_ACCEPTABLE_SCORE",
    "RESULT_DELIMITER",
]
