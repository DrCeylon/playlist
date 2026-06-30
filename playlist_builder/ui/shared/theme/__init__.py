"""Theme engine — ThemeRegistry, ThemeManager, bundled design tokens."""

from playlist_builder.ui.shared.theme.loader import (
    ThemeLoadError,
    bundled_themes_dir,
    load_bundled_definitions,
    load_theme_file,
    resolve_definitions,
)
from playlist_builder.ui.shared.theme.manager import DEFAULT_THEME_ID, ThemeManager
from playlist_builder.ui.shared.theme.models import (
    Theme,
    ThemeDefinition,
    ThemeError,
    ThemeNotFoundError,
    theme_to_option,
)
from playlist_builder.ui.shared.theme.registry import ThemeRegistry, ThemeValidationError, ThemeValidationReport
from playlist_builder.ui.shared.theme.tokens import DesignTokens
from playlist_builder.ui.shared.theme.validation import (
    REQUIRED_COLOR_KEYS,
    REQUIRED_RADIUS_KEYS,
    REQUIRED_SHADOW_KEYS,
    REQUIRED_SPACING_KEYS,
    REQUIRED_TYPOGRAPHY_KEYS,
    is_valid_color,
    validate_theme,
    validate_tokens,
)

__all__ = [
    "DEFAULT_THEME_ID",
    "DesignTokens",
    "REQUIRED_COLOR_KEYS",
    "REQUIRED_RADIUS_KEYS",
    "REQUIRED_SHADOW_KEYS",
    "REQUIRED_SPACING_KEYS",
    "REQUIRED_TYPOGRAPHY_KEYS",
    "Theme",
    "ThemeDefinition",
    "ThemeError",
    "ThemeLoadError",
    "ThemeManager",
    "ThemeNotFoundError",
    "ThemeRegistry",
    "ThemeValidationError",
    "ThemeValidationReport",
    "bundled_themes_dir",
    "is_valid_color",
    "load_bundled_definitions",
    "load_theme_file",
    "resolve_definitions",
    "theme_to_option",
    "validate_theme",
    "validate_tokens",
]
