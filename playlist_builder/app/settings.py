from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Central configuration for application use cases."""

    country_code: str = "fr"
    catalog_cache_path: Path = Path("cache/itunes_catalog.json")
    identity_cache_path: Path = Path("cache/apple_music_identity.json")
    acquire_missing_from_catalog: bool = True
    wait_for_manual_catalog_add: bool = False
    catalog_acquisition_min_confidence: float = 70.0
    use_catalog_cache: bool = True
