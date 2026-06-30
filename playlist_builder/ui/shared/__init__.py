"""Provider-neutral shared UI contracts (DTO, state, validation)."""

from playlist_builder.ui.shared.dto import (
    DiagnosticEvent,
    EnergyCurveOption,
    ExclusionRule,
    ImportProgressState,
    ImportResultState,
    PlaylistGenerationRequest,
    PlaylistGenerationResult,
    ProviderOption,
    ThemeOption,
    UserPreferences,
)
from playlist_builder.ui.shared.navigation import AppRoute
from playlist_builder.ui.shared.state import UiScreenState

__all__ = [
    "AppRoute",
    "DiagnosticEvent",
    "EnergyCurveOption",
    "ExclusionRule",
    "ImportProgressState",
    "ImportResultState",
    "PlaylistGenerationRequest",
    "PlaylistGenerationResult",
    "ProviderOption",
    "ThemeOption",
    "UiScreenState",
    "UserPreferences",
]
