from __future__ import annotations

import re
from typing import Final

from playlist_builder.ui.shared.theme.models import Theme
from playlist_builder.ui.shared.theme.tokens import DesignTokens
from playlist_builder.ui.shared.validation import ValidationError, ValidationResult, merge_results

_COLOR_PATTERN: Final[re.Pattern[str]] = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")

REQUIRED_COLOR_KEYS: Final[tuple[str, ...]] = (
    "color.background.primary",
    "color.background.secondary",
    "color.background.elevated",
    "color.surface",
    "color.text.primary",
    "color.text.secondary",
    "color.text.tertiary",
    "color.accent.primary",
    "color.accent.secondary",
    "color.border.subtle",
    "color.input.background",
    "color.input.text",
    "color.sidebar.background",
    "color.sidebar.text",
    "color.status.success",
    "color.status.warning",
    "color.status.error",
    "color.status.info",
    "color.lab.accent",
)

REQUIRED_TYPOGRAPHY_KEYS: Final[tuple[str, ...]] = (
    "font.largeTitle",
    "font.title",
    "font.headline",
    "font.body",
    "font.callout",
    "font.caption",
    "font.mono",
)

REQUIRED_SPACING_KEYS: Final[tuple[str, ...]] = (
    "space.xs",
    "space.sm",
    "space.md",
    "space.lg",
    "space.xl",
    "space.xxl",
)

REQUIRED_RADIUS_KEYS: Final[tuple[str, ...]] = (
    "radius.sm",
    "radius.md",
    "radius.lg",
    "radius.xl",
)

REQUIRED_SHADOW_KEYS: Final[tuple[str, ...]] = (
    "shadow.card",
    "shadow.elevated",
)

KNOWN_COLOR_KEYS: Final[frozenset[str]] = frozenset(REQUIRED_COLOR_KEYS)
KNOWN_TYPOGRAPHY_KEYS: Final[frozenset[str]] = frozenset(REQUIRED_TYPOGRAPHY_KEYS)
KNOWN_SPACING_KEYS: Final[frozenset[str]] = frozenset(REQUIRED_SPACING_KEYS)
KNOWN_RADIUS_KEYS: Final[frozenset[str]] = frozenset(REQUIRED_RADIUS_KEYS)
KNOWN_SHADOW_KEYS: Final[frozenset[str]] = frozenset(REQUIRED_SHADOW_KEYS)


def is_valid_color(value: str) -> bool:
    return bool(_COLOR_PATTERN.match(value))


def validate_theme_identity(theme: Theme) -> ValidationResult:
    errors: list[ValidationError] = []
    if not theme.id.strip():
        errors.append(ValidationError("id", "L'identifiant du thème est requis."))
    if not theme.display_name.strip():
        errors.append(ValidationError("display_name", "Le nom affiché du thème est requis."))
    if not theme.version.strip():
        errors.append(ValidationError("version", "La version du thème est requise."))
    return ValidationResult(errors=tuple(errors))


def validate_tokens(tokens: DesignTokens) -> ValidationResult:
    return merge_results(
        _validate_required_keys(tokens),
        _validate_color_values(tokens),
        _validate_non_negative_integers(tokens),
    )


def collect_unknown_token_warnings(tokens: DesignTokens) -> tuple[str, ...]:
    warnings: list[str] = []
    for key in tokens.colors:
        if key not in KNOWN_COLOR_KEYS:
            warnings.append(f"colors.{key}")
    for key in tokens.typography:
        if key not in KNOWN_TYPOGRAPHY_KEYS:
            warnings.append(f"typography.{key}")
    for key in tokens.spacing:
        if key not in KNOWN_SPACING_KEYS:
            warnings.append(f"spacing.{key}")
    for key in tokens.radius:
        if key not in KNOWN_RADIUS_KEYS:
            warnings.append(f"radius.{key}")
    for key in tokens.shadows:
        if key not in KNOWN_SHADOW_KEYS:
            warnings.append(f"shadows.{key}")
    return tuple(warnings)


def validate_theme(theme: Theme) -> ValidationResult:
    return merge_results(validate_theme_identity(theme), validate_tokens(theme.tokens))


def _validate_required_keys(tokens: DesignTokens) -> ValidationResult:
    errors: list[ValidationError] = []
    for key in REQUIRED_COLOR_KEYS:
        if key not in tokens.colors:
            errors.append(ValidationError(f"tokens.colors.{key}", "Jeton de couleur requis manquant."))
    for key in REQUIRED_TYPOGRAPHY_KEYS:
        if key not in tokens.typography:
            errors.append(ValidationError(f"tokens.typography.{key}", "Jeton typographique requis manquant."))
    for key in REQUIRED_SPACING_KEYS:
        if key not in tokens.spacing:
            errors.append(ValidationError(f"tokens.spacing.{key}", "Jeton d'espacement requis manquant."))
    for key in REQUIRED_RADIUS_KEYS:
        if key not in tokens.radius:
            errors.append(ValidationError(f"tokens.radius.{key}", "Jeton de rayon requis manquant."))
    for key in REQUIRED_SHADOW_KEYS:
        if key not in tokens.shadows:
            errors.append(ValidationError(f"tokens.shadows.{key}", "Jeton d'ombre requis manquant."))
    return ValidationResult(errors=tuple(errors))


def _validate_color_values(tokens: DesignTokens) -> ValidationResult:
    errors: list[ValidationError] = []
    for key, value in tokens.colors.items():
        if not isinstance(value, str) or not is_valid_color(value):
            errors.append(
                ValidationError(
                    f"tokens.colors.{key}",
                    "La couleur doit être au format #RRGGBB ou #RRGGBBAA.",
                )
            )
    return ValidationResult(errors=tuple(errors))


def _validate_non_negative_integers(tokens: DesignTokens) -> ValidationResult:
    errors: list[ValidationError] = []
    for group_name, group in (("spacing", tokens.spacing), ("radius", tokens.radius)):
        for key, value in group.items():
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(
                    ValidationError(
                        f"tokens.{group_name}.{key}",
                        "La valeur doit être un entier.",
                    )
                )
            elif value < 0:
                errors.append(
                    ValidationError(
                        f"tokens.{group_name}.{key}",
                        "La valeur doit être supérieure ou égale à 0.",
                    )
                )
    return ValidationResult(errors=tuple(errors))
