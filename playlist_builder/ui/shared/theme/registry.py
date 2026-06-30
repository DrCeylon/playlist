from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.ui.shared.theme.loader import load_bundled_definitions, resolve_definitions
from playlist_builder.ui.shared.theme.models import Theme, ThemeError, ThemeNotFoundError
from playlist_builder.ui.shared.theme.validation import collect_unknown_token_warnings, validate_theme
from playlist_builder.ui.shared.validation import ValidationResult


class ThemeValidationError(ThemeError):
    """Raised when a theme fails structural validation."""

    def __init__(self, result: ValidationResult) -> None:
        joined = "; ".join(f"{error.field}: {error.message}" for error in result.errors)
        super().__init__(joined)
        self.result = result


@dataclass(frozen=True, slots=True)
class ThemeValidationReport:
    result: ValidationResult
    warnings: tuple[str, ...] = ()


class ThemeRegistry:
    """In-memory registry of resolved themes."""

    def __init__(self, themes: dict[str, Theme] | None = None) -> None:
        self._themes: dict[str, Theme] = dict(themes or {})

    @classmethod
    def load_bundled(cls) -> ThemeRegistry:
        definitions = load_bundled_definitions()
        themes = resolve_definitions(definitions)
        registry = cls()
        for theme in themes:
            registry.register(theme)
        return registry

    def register(self, theme: Theme) -> None:
        report = self.validate(theme)
        if not report.result.is_valid:
            raise ThemeValidationError(report.result)
        self._themes[theme.id] = theme

    def get(self, theme_id: str) -> Theme:
        theme = self._themes.get(theme_id)
        if theme is None:
            raise ThemeNotFoundError(theme_id)
        return theme

    def list(self) -> tuple[Theme, ...]:
        return tuple(self._themes[theme_id] for theme_id in sorted(self._themes))

    def validate(self, theme: Theme) -> ThemeValidationReport:
        result = validate_theme(theme)
        warnings = collect_unknown_token_warnings(theme.tokens)
        return ThemeValidationReport(result=result, warnings=warnings)
