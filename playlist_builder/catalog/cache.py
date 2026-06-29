"""Backward-compatible JSON cache facade.

New code should import from :mod:`playlist_builder.infrastructure.cache`.
"""

from __future__ import annotations

from playlist_builder.infrastructure.cache.store import JsonCache

__all__ = ["JsonCache"]
