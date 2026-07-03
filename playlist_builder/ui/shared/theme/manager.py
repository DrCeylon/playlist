from __future__ import annotations

from collections.abc import Callable

from playlist_builder.ui.shared.theme.models import Theme
from playlist_builder.ui.shared.theme.registry import ThemeRegistry

SYSTEM_THEME_ID = "system"
LIGHT_THEME_ID = "apple_music_light"
DARK_THEME_ID = "apple_music_dark"
DEFAULT_THEME_ID = SYSTEM_THEME_ID


def resolve_theme_id(selected_id: str, *, dark: bool = False) -> str:
    if selected_id == SYSTEM_THEME_ID:
        return DARK_THEME_ID if dark else LIGHT_THEME_ID
    return selected_id


class ThemeManager:
    """Tracks the active theme and notifies subscribers on change."""

    def __init__(
        self,
        registry: ThemeRegistry,
        *,
        default_theme_id: str = DEFAULT_THEME_ID,
        dark: bool = False,
    ) -> None:
        self._registry = registry
        self._selected_theme_id = default_theme_id
        self._dark = dark
        self._active = registry.get(resolve_theme_id(default_theme_id, dark=dark))
        self._subscribers: list[Callable[[Theme], None]] = []

    @property
    def active(self) -> Theme:
        return self._active

    @property
    def selected_theme_id(self) -> str:
        return self._selected_theme_id

    def apply(self, theme_id: str, *, dark: bool | None = None) -> None:
        if dark is not None:
            self._dark = dark
        resolved_id = resolve_theme_id(theme_id, dark=self._dark)
        theme = self._registry.get(resolved_id)
        if theme.id == self._active.id and theme_id == self._selected_theme_id:
            return
        self._selected_theme_id = theme_id
        self._active = theme
        for callback in tuple(self._subscribers):
            callback(theme)

    def set_dark(self, dark: bool) -> None:
        if self._selected_theme_id != SYSTEM_THEME_ID:
            return
        resolved_id = resolve_theme_id(self._selected_theme_id, dark=dark)
        if resolved_id == self._active.id and dark == self._dark:
            return
        self._dark = dark
        self._active = self._registry.get(resolved_id)
        for callback in tuple(self._subscribers):
            callback(self._active)

    def subscribe(self, callback: Callable[[Theme], None]) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Theme], None]) -> None:
        try:
            self._subscribers.remove(callback)
        except ValueError:
            return
