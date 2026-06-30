from __future__ import annotations

from collections.abc import Callable

from playlist_builder.ui.shared.theme.models import Theme, ThemeNotFoundError
from playlist_builder.ui.shared.theme.registry import ThemeRegistry

DEFAULT_THEME_ID = "apple_music_light"


class ThemeManager:
    """Tracks the active theme and notifies subscribers on change."""

    def __init__(
        self,
        registry: ThemeRegistry,
        *,
        default_theme_id: str = DEFAULT_THEME_ID,
    ) -> None:
        self._registry = registry
        self._active = registry.get(default_theme_id)
        self._subscribers: list[Callable[[Theme], None]] = []

    @property
    def active(self) -> Theme:
        return self._active

    def apply(self, theme_id: str) -> None:
        theme = self._registry.get(theme_id)
        if theme.id == self._active.id:
            return
        self._active = theme
        for callback in tuple(self._subscribers):
            callback(theme)

    def subscribe(self, callback: Callable[[Theme], None]) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Theme], None]) -> None:
        try:
            self._subscribers.remove(callback)
        except ValueError:
            return
