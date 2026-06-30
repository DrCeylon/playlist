from __future__ import annotations

from dataclasses import dataclass, field

from playlist_builder.ui.shared.dto.enums import DiagnosticLevel


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    phase: str
    message: str
    level: DiagnosticLevel = DiagnosticLevel.INFO
    timestamp_iso: str = ""
    payload: tuple[tuple[str, str], ...] = field(default_factory=tuple)
