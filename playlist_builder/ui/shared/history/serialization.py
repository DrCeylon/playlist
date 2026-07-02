from __future__ import annotations

from typing import Any

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.history.models import (
    HistoryDiagnosticsSummary,
    HistorySessionStatus,
    SessionHistoryRecord,
)

SCHEMA_VERSION = 1


def record_to_dict(record: SessionHistoryRecord) -> dict[str, Any]:
    payload = {
        "session_id": record.session_id,
        "started_at_iso": record.started_at_iso,
        "finished_at_iso": record.finished_at_iso,
        "playlist_name": record.playlist_name,
        "provider_id": record.provider_id.value,
        "status": record.status.value,
        "track_count": record.track_count,
        "added_count": record.added_count,
        "skipped_count": record.skipped_count,
        "not_found_count": record.not_found_count,
        "error_count": record.error_count,
        "duration_ms": record.duration_ms,
        "text_report_path": record.text_report_path,
        "json_report_path": record.json_report_path,
        "diagnostics": {
            "warnings": record.diagnostics.warnings,
            "errors": record.diagnostics.errors,
            "last_message": record.diagnostics.last_message,
        },
        "generation_request": _sanitize(record.generation_request),
        "generation_result": _sanitize(record.generation_result),
        "import_result": _sanitize(record.import_result),
    }
    return payload


def record_from_dict(payload: dict[str, Any]) -> SessionHistoryRecord:
    diagnostics_raw = payload.get("diagnostics", {})
    if not isinstance(diagnostics_raw, dict):
        diagnostics_raw = {}
    provider_raw = str(payload.get("provider_id", ProviderId.APPLE_MUSIC.value))
    try:
        provider = ProviderId(provider_raw)
    except ValueError:
        provider = ProviderId.APPLE_MUSIC
    status_raw = str(payload.get("status", HistorySessionStatus.FAILED.value))
    try:
        status = HistorySessionStatus(status_raw)
    except ValueError:
        status = HistorySessionStatus.FAILED
    return SessionHistoryRecord(
        session_id=str(payload.get("session_id", "")),
        started_at_iso=str(payload.get("started_at_iso", "")),
        finished_at_iso=_optional_str(payload.get("finished_at_iso")),
        playlist_name=str(payload.get("playlist_name", "")),
        provider_id=provider,
        status=status,
        track_count=int(payload.get("track_count", 0) or 0),
        added_count=int(payload.get("added_count", 0) or 0),
        skipped_count=int(payload.get("skipped_count", 0) or 0),
        not_found_count=int(payload.get("not_found_count", 0) or 0),
        error_count=int(payload.get("error_count", 0) or 0),
        duration_ms=_optional_int(payload.get("duration_ms")),
        text_report_path=str(payload.get("text_report_path", "")),
        json_report_path=str(payload.get("json_report_path", "")),
        diagnostics=HistoryDiagnosticsSummary(
            warnings=int(diagnostics_raw.get("warnings", 0) or 0),
            errors=int(diagnostics_raw.get("errors", 0) or 0),
            last_message=str(diagnostics_raw.get("last_message", "")),
        ),
        generation_request=_optional_dict(payload.get("generation_request")),
        generation_result=_optional_dict(payload.get("generation_result")),
        import_result=_optional_dict(payload.get("import_result")),
    )


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_dict(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return _sanitize(value)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() == "persistent_id":
                continue
            payload[str(key)] = _sanitize(item)
        return payload
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value

