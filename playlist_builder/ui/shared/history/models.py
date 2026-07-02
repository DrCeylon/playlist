from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from playlist_builder.canonical.enums import ProviderId


class HistorySessionStatus(StrEnum):
    GENERATED = "generated"
    IMPORTED = "imported"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    WAITING_FOR_MANUAL_ACQUISITION = "waiting_for_manual_acquisition"


@dataclass(frozen=True, slots=True)
class HistoryDiagnosticsSummary:
    warnings: int = 0
    errors: int = 0
    last_message: str = ""


@dataclass(frozen=True, slots=True)
class SessionHistoryRecord:
    session_id: str
    started_at_iso: str
    finished_at_iso: str | None
    playlist_name: str
    provider_id: ProviderId
    status: HistorySessionStatus
    track_count: int
    added_count: int
    skipped_count: int
    not_found_count: int
    error_count: int
    duration_ms: int | None
    text_report_path: str = ""
    json_report_path: str = ""
    diagnostics: HistoryDiagnosticsSummary = HistoryDiagnosticsSummary()
    generation_request: dict[str, Any] | None = None
    generation_result: dict[str, Any] | None = None
    import_result: dict[str, Any] | None = None

    @property
    def finished(self) -> bool:
        return bool(self.finished_at_iso)

    @staticmethod
    def now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")

