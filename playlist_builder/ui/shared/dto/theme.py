from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ThemeOption:
    theme_id: str
    display_name: str
    preview_background: str = ""
    preview_accent: str = ""
