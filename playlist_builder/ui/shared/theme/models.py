from __future__ import annotations

from dataclasses import dataclass, field

from playlist_builder.ui.shared.dto.theme import ThemeOption
from playlist_builder.ui.shared.theme.tokens import DesignTokens


@dataclass(frozen=True, slots=True)
class Theme:
    """Resolved theme with merged tokens ready for runtime use."""

    id: str
    display_name: str
    version: str
    tokens: DesignTokens
    metadata: dict[str, str] = field(default_factory=dict)
    extends: str | None = None


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    """Parsed theme file before parent/child token resolution."""

    id: str
    display_name: str
    version: str
    tokens: DesignTokens
    metadata: dict[str, str] = field(default_factory=dict)
    extends: str | None = None


class ThemeError(Exception):
    """Base error for theme engine failures."""


class ThemeNotFoundError(ThemeError):
    """Raised when a theme id is unknown to the registry."""

    def __init__(self, theme_id: str) -> None:
        super().__init__(f"Thème inconnu : {theme_id!r}.")
        self.theme_id = theme_id


def theme_to_option(theme: Theme) -> ThemeOption:
    """Map a resolved theme to the UI selector DTO."""

    return ThemeOption(
        theme_id=theme.id,
        display_name=theme.display_name,
        preview_background=theme.tokens.colors["color.background.primary"],
        preview_accent=theme.tokens.colors["color.accent.primary"],
    )
