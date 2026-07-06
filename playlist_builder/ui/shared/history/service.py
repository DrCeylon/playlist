from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto import ImportResultState
from playlist_builder.ui.shared.history.models import (
    HistoryDiagnosticsSummary,
    HistorySessionStatus,
    SessionHistoryRecord,
)
from playlist_builder.ui.shared.history.repository import SessionHistoryRepository


class SessionHistoryService:
    def __init__(self, repository: SessionHistoryRepository) -> None:
        self._repository = repository
        self._started_perf: dict[str, float] = {}

    def create_generation_session(
        self,
        *,
        request_id: str,
        playlist_name: str,
        provider_id: ProviderId,
        generation_request: dict[str, Any] | None,
        generation_result: dict[str, Any] | None,
        track_count: int,
    ) -> SessionHistoryRecord:
        session_id = f"hist-{uuid4()}"
        started_at = datetime.now().isoformat(timespec="seconds")
        self._started_perf[session_id] = perf_counter()
        record = SessionHistoryRecord(
            session_id=session_id,
            started_at_iso=started_at,
            finished_at_iso=started_at,
            playlist_name=playlist_name,
            provider_id=provider_id,
            status=HistorySessionStatus.GENERATED,
            track_count=track_count,
            added_count=0,
            skipped_count=0,
            not_found_count=0,
            error_count=0,
            duration_ms=0,
            generation_request=generation_request,
            generation_result=generation_result,
        )
        return self._repository.upsert(record)

    def attach_import_result(
        self,
        *,
        session_id: str | None,
        playlist_name: str,
        provider_id: ProviderId,
        result: ImportResultState,
        json_report_path: str = "",
        text_report_path: str = "",
        diagnostics: HistoryDiagnosticsSummary | None = None,
    ) -> SessionHistoryRecord:
        existing = self._repository.get_session(session_id or "")
        if existing is None:
            existing = SessionHistoryRecord(
                session_id=session_id or f"hist-{uuid4()}",
                started_at_iso=datetime.now().isoformat(timespec="seconds"),
                finished_at_iso=None,
                playlist_name=playlist_name,
                provider_id=provider_id,
                status=HistorySessionStatus.GENERATED,
                track_count=0,
                added_count=0,
                skipped_count=0,
                not_found_count=0,
                error_count=0,
                duration_ms=None,
            )
        duration_ms = self._duration_ms(existing.session_id)
        status = _status_from_import_phase(result.phase.value)
        updated = replace(
            existing,
            finished_at_iso=datetime.now().isoformat(timespec="seconds"),
            status=status,
            track_count=len(result.outcomes),
            added_count=result.added_count,
            skipped_count=sum(1 for item in result.outcomes if item.status.value == "skipped"),
            not_found_count=result.not_found_count,
            error_count=sum(1 for item in result.outcomes if item.status.value == "error"),
            duration_ms=duration_ms,
            text_report_path=text_report_path or existing.text_report_path,
            json_report_path=json_report_path or existing.json_report_path,
            diagnostics=diagnostics or existing.diagnostics,
            import_result=_import_result_dict(result),
        )
        return self._repository.upsert(updated)

    def mark_failed(self, *, session_id: str, message: str) -> SessionHistoryRecord | None:
        existing = self._repository.get_session(session_id)
        if existing is None:
            return None
        updated = replace(
            existing,
            finished_at_iso=datetime.now().isoformat(timespec="seconds"),
            status=HistorySessionStatus.FAILED,
            duration_ms=self._duration_ms(session_id),
            diagnostics=HistoryDiagnosticsSummary(
                warnings=existing.diagnostics.warnings,
                errors=existing.diagnostics.errors + 1,
                last_message=message,
            ),
        )
        return self._repository.upsert(updated)

    def list_sessions(self) -> list[SessionHistoryRecord]:
        return self._repository.list_sessions()

    def get_session(self, session_id: str) -> SessionHistoryRecord | None:
        return self._repository.get_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        return self._repository.delete_session(session_id)

    def clear(self) -> None:
        self._repository.clear()

    def export_session(self, session_id: str) -> dict[str, Any] | None:
        session = self._repository.get_session(session_id)
        if session is None:
            return None
        return {
            "session_id": session.session_id,
            "playlist_name": session.playlist_name,
            "provider_id": session.provider_id.value,
            "status": session.status.value,
            "text_report_path": session.text_report_path,
            "json_report_path": session.json_report_path,
            "generation_request": session.generation_request or {},
            "generation_result": session.generation_result or {},
            "import_result": session.import_result or {},
        }

    def _duration_ms(self, session_id: str) -> int | None:
        started = self._started_perf.pop(session_id, None)
        if started is None:
            return None
        return int((perf_counter() - started) * 1000)


def _status_from_import_phase(phase: str) -> HistorySessionStatus:
    if phase == "completed":
        return HistorySessionStatus.IMPORTED
    if phase == "partial_success":
        return HistorySessionStatus.PARTIAL_SUCCESS
    if phase == "waiting_for_manual_acquisition":
        return HistorySessionStatus.WAITING_FOR_MANUAL_ACQUISITION
    if phase == "failed":
        return HistorySessionStatus.FAILED
    return HistorySessionStatus.IMPORTED


def _import_result_dict(result: ImportResultState) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "playlist_name": result.playlist_name,
        "phase": result.phase.value,
        "outcomes": [
            {
                "artist": item.artist,
                "title": item.title,
                "section": item.section,
                "status": item.status.value,
                "message": item.message,
            }
            for item in result.outcomes
        ],
    }
    if result.import_session_id:
        payload["import_session_id"] = result.import_session_id
    if result.manual_token:
        payload["manual_token"] = result.manual_token
    if result.manual_artist:
        payload["manual_artist"] = result.manual_artist
    if result.manual_title:
        payload["manual_title"] = result.manual_title
    if result.manual_instructions:
        payload["manual_instructions"] = result.manual_instructions
    if result.manual_catalog_label:
        payload["manual_catalog_label"] = result.manual_catalog_label
    if result.manual_catalog_url:
        payload["manual_catalog_url"] = result.manual_catalog_url
    if result.manual_album:
        payload["manual_album"] = result.manual_album
    return payload

