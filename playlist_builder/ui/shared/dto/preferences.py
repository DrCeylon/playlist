from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from playlist_builder.canonical.enums import ProviderId


@dataclass(frozen=True, slots=True)
class UserPreferences:
    default_provider_id: ProviderId = ProviderId.APPLE_MUSIC
    country_code: str = "fr"
    theme_id: str = "apple_music_light"
    locale: str = "fr"
    acquire_missing_from_catalog: bool = True
    wait_for_manual_catalog_add: bool = False
    architect_mode_default: bool = False
    identity_cache_path: Path = Path("cache/apple_music_identity.json")
    catalog_cache_path: Path = Path("cache/itunes_catalog.json")
    use_catalog_cache: bool = True
