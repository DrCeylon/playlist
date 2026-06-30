from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DesignTokens:
    """Resolved design token values for a theme."""

    colors: dict[str, str]
    typography: dict[str, str]
    spacing: dict[str, int]
    radius: dict[str, int]
    shadows: dict[str, str]

    def merge(self, override: DesignTokens) -> DesignTokens:
        """Return a new token set with override values applied on top."""

        return DesignTokens(
            colors={**self.colors, **override.colors},
            typography={**self.typography, **override.typography},
            spacing={**self.spacing, **override.spacing},
            radius={**self.radius, **override.radius},
            shadows={**self.shadows, **override.shadows},
        )

    @classmethod
    def empty(cls) -> DesignTokens:
        return cls(
            colors={},
            typography={},
            spacing={},
            radius={},
            shadows={},
        )
