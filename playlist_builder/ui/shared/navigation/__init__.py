from __future__ import annotations

from enum import StrEnum


class AppRoute(StrEnum):
    """Abstract navigation destinations (macOS sidebar / iOS tabs)."""

    HOME = "home"
    NEW_PLAYLIST = "new_playlist"
    PREVIEW = "preview"
    IMPORT = "import"
    HISTORY = "history"
    HISTORY_DETAIL = "history_detail"
    PLAYLISTS = "playlists"
    PLAYLIST_DETAIL = "playlist_detail"
    SYNC = "sync"
    PROVIDERS = "providers"
    DIAGNOSTICS = "diagnostics"
    SETTINGS = "settings"
    SETTINGS_THEME = "settings_theme"
    SETTINGS_PROVIDER = "settings_provider"
    MANUAL_ACQUISITION = "manual_acquisition"
