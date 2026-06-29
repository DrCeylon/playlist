from __future__ import annotations

FIELD_DELIMITER = "\x1e"
RESULT_DELIMITER = "\x1f"
MAX_QUERY_VARIANTS = 6
MIN_ACCEPTABLE_SCORE = 55

_GENERIC_SECTIONS = frozenset({"playlist", "generated", "discovery"})
