"""Backward-compatible text normalization facade.

New code should import from :mod:`playlist_builder.scoring.normalization`.
"""

from __future__ import annotations

from playlist_builder.scoring.normalization import normalize_text, token_set

__all__ = ["normalize_text", "token_set"]
