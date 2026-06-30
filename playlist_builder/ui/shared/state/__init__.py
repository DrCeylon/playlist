from __future__ import annotations

from enum import StrEnum


class UiScreenState(StrEnum):
    """High-level UI session states shared across platforms."""

    IDLE = "idle"
    EDITING = "editing"
    GENERATING = "generating"
    GENERATED = "generated"
    IMPORTING = "importing"
    WAITING_FOR_MANUAL_ACQUISITION = "waiting_for_manual_acquisition"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
