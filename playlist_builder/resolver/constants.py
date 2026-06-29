from __future__ import annotations

FIELD_DELIMITER = "\x1e"
CANDIDATE_DELIMITER = "\x1d"
RESULT_DELIMITER = "\x1f"
MAX_QUERY_VARIANTS = 6
MAX_CANDIDATES_PER_TRACK = 12
MIN_ACCEPTABLE_SCORE = 55

_GENERIC_SECTIONS = frozenset({"playlist", "generated", "discovery"})
