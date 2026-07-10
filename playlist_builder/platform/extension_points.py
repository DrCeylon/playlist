from __future__ import annotations

from enum import StrEnum


class ExtensionPointId(StrEnum):
    """Stable extension point identifiers — host dispatches by ID, never by import path.

    Only points marked *active* have a registry in the host today. Others are
    reserved names for future tiers (see ADR-020).
    """

    # Active today (in-process registration via factory or ThemeRegistry)
    MUSIC_PROVIDER = "music_provider"
    THEME = "theme"
    DISCOVERY_CANDIDATE = "discovery_candidate"

    # Reserved — documented contract only until epic ships (YAGNI: no loader)
    SYNC_STRATEGY = "sync_strategy"
    CONFLICT_RESOLVER = "conflict_resolver"
    AUTOMATION_RULE = "automation_rule"
    AI_ENGINE = "ai_engine"
    EXPORT_FORMAT = "export_format"
    IMPORT_FORMAT = "import_format"
    DASHBOARD_WIDGET = "dashboard_widget"
    ANALYSIS_TOOL = "analysis_tool"


ACTIVE_EXTENSION_POINTS: frozenset[ExtensionPointId] = frozenset(
    {
        ExtensionPointId.MUSIC_PROVIDER,
        ExtensionPointId.THEME,
        ExtensionPointId.DISCOVERY_CANDIDATE,
    }
)
