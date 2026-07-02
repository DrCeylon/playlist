"""WCAG 2.x contrast helpers shared with ResonanceDesign ThemeContrast."""

from __future__ import annotations

import math
from typing import Final

MINIMUM_CONTRAST_RATIO: Final[float] = 4.5


def _channel(value: float) -> float:
    if value <= 0.03928:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float | None:
    value = hex_color.strip()
    if value.startswith("#"):
        value = value[1:]
    if len(value) not in {6, 8}:
        return None
    try:
        numeric = int(value, 16)
    except ValueError:
        return None

    if len(value) == 6:
        red = (numeric >> 16) & 0xFF
        green = (numeric >> 8) & 0xFF
        blue = numeric & 0xFF
    else:
        red = (numeric >> 24) & 0xFF
        green = (numeric >> 16) & 0xFF
        blue = (numeric >> 8) & 0xFF

    red_n = _channel(red / 255.0)
    green_n = _channel(green / 255.0)
    blue_n = _channel(blue / 255.0)
    return 0.2126 * red_n + 0.7152 * green_n + 0.0722 * blue_n


def contrast_ratio(foreground_hex: str, background_hex: str) -> float | None:
    foreground = relative_luminance(foreground_hex)
    background = relative_luminance(background_hex)
    if foreground is None or background is None:
        return None
    lighter = max(foreground, background)
    darker = min(foreground, background)
    return (lighter + 0.05) / (darker + 0.05)


def has_readable_contrast(foreground_hex: str, background_hex: str) -> bool:
    ratio = contrast_ratio(foreground_hex, background_hex)
    if ratio is None:
        return False
    return ratio >= MINIMUM_CONTRAST_RATIO
