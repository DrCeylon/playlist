"""Apple Music catalog acquisition policy (Phase 5.3.3 decision)."""

from __future__ import annotations

from enum import StrEnum

# S2 (open → play → duplicate) is deprecated for production after macOS experiments.
# See wiki/Phase-5-3-3-Acquisition-Experiments.md and ADR-010.
ENABLE_PLAY_DUPLICATE_ACQUISITION_DEFAULT = False

# Quick library probe after a successful add-URL only (not the old 6×5s automatic loop).
PRODUCTION_ADDED_LIBRARY_PROBE_ATTEMPTS = 2


class CatalogAcquisitionMode(StrEnum):
    """How production resolves catalog tracks missing from the local library."""

    PRODUCTION = "production"
    """Quick add-URL attempt, then manual acquisition (no S2 duplicate path)."""

    LEGACY_EXPERIMENTAL = "legacy_experimental"
    """Full acquire_song_from_url including S2 — experiments/CLI opt-in only."""
