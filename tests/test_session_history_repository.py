from __future__ import annotations

import threading
from pathlib import Path

import pytest

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.history.errors import UnsupportedSchemaVersionError
from playlist_builder.ui.shared.history.models import HistorySessionStatus, SessionHistoryRecord
from playlist_builder.ui.shared.history.repository import SessionHistoryRepository
from playlist_builder.ui.shared.history.serialization import SCHEMA_VERSION


def _sample_record(session_id: str, name: str) -> SessionHistoryRecord:
    return SessionHistoryRecord(
        session_id=session_id,
        started_at_iso="2026-07-02T08:00:00",
        finished_at_iso="2026-07-02T08:00:05",
        playlist_name=name,
        provider_id=ProviderId.APPLE_MUSIC,
        status=HistorySessionStatus.GENERATED,
        track_count=1,
        added_count=0,
        skipped_count=0,
        not_found_count=0,
        error_count=0,
        duration_ms=1000,
    )


def test_session_history_repository_rejects_forward_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "sessions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'{{"schema_version": {SCHEMA_VERSION + 1}, "sessions": []}}',
        encoding="utf-8",
    )
    repository = SessionHistoryRepository(path)
    with pytest.raises(UnsupportedSchemaVersionError):
        repository.list_sessions()


def test_session_history_repository_concurrent_upserts_preserve_all_records(tmp_path: Path) -> None:
    repository = SessionHistoryRepository(tmp_path / "sessions.json")
    barrier = threading.Barrier(2)

    def upsert(session_id: str, name: str) -> None:
        barrier.wait(timeout=5)
        repository.upsert(_sample_record(session_id, name))

    threads = [
        threading.Thread(target=upsert, args=("hist-a", "Session A")),
        threading.Thread(target=upsert, args=("hist-b", "Session B")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    session_ids = {item.session_id for item in repository.list_sessions()}
    assert session_ids == {"hist-a", "hist-b"}
