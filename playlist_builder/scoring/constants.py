from __future__ import annotations

# Catalog / API matching thresholds (0-100 scale).
MIN_MATCH_SCORE = 30
MIN_MUSICKIT_MATCH_SCORE = 60

# Fuzzy resolution threshold (0-100 scale).
MIN_ACCEPTABLE_SCORE = 55

# Planning constraint adjustments (unbounded float scale).
EXCLUSION_PENALTY = -10_000
INCLUSION_BOOST = 20

# Fuzzy match weight distribution (must sum to 100).
FUZZY_TITLE_SIMILARITY_WEIGHT = 45
FUZZY_TITLE_TOKEN_WEIGHT = 25
FUZZY_ARTIST_SIMILARITY_WEIGHT = 20
FUZZY_ARTIST_TOKEN_WEIGHT = 10

# Catalog substring match weight distribution (must sum to 100).
CATALOG_ARTIST_EXACT_WEIGHT = 50
CATALOG_ARTIST_PARTIAL_WEIGHT = 30
CATALOG_TITLE_EXACT_WEIGHT = 50
CATALOG_TITLE_PARTIAL_WEIGHT = 30

PREFERRED_TERM_BOOST = 10
