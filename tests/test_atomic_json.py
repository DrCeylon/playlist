from __future__ import annotations

import json
import threading
from pathlib import Path

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.app.playlist_library.json_repository import JsonManagedPlaylistRepository
from playlist_builder.infrastructure.atomic_json import advisory_file_lock, locked_json_document, replace_file_atomic
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary


def test_locked_json_document_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "store.json"
    with locked_json_document(target) as payload:
        payload["value"] = 42
    assert json.loads(target.read_text(encoding="utf-8"))["value"] == 42


def test_json_repository_concurrent_upserts_preserve_all_records(tmp_path: Path) -> None:
    repository = JsonManagedPlaylistRepository(tmp_path / "managed_playlists.json")
    barrier = threading.Barrier(2)

    def upsert(playlist_id: str, name: str) -> None:
        barrier.wait(timeout=5)
        repository.upsert(
            ManagedPlaylistDetail(
                summary=ManagedPlaylistSummary(
                    local_playlist_id=playlist_id,
                    name=name,
                    provider_id=ProviderId.APPLE_MUSIC,
                    track_count=1,
                    sync_status="pending",
                )
            )
        )

    threads = [
        threading.Thread(target=upsert, args=("local-a", "Playlist A")),
        threading.Thread(target=upsert, args=("local-b", "Playlist B")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    playlists = repository.list_playlists()
    ids = {item.summary.local_playlist_id for item in playlists}
    assert ids == {"local-a", "local-b"}


def test_replace_file_atomic_publishes_complete_file(tmp_path: Path) -> None:
    target = tmp_path / "immutable.json"
    replace_file_atomic(target, '{"checksum": "abc"}')
    assert target.read_text(encoding="utf-8") == '{"checksum": "abc"}'


def test_advisory_file_lock_serializes_concurrent_publish(tmp_path: Path) -> None:
    target = tmp_path / "shared.json"
    lock_path = target.with_suffix(".json.lock")
    barrier = threading.Barrier(2)
    seen: list[str] = []

    def publish(value: str) -> None:
        barrier.wait(timeout=5)
        with advisory_file_lock(lock_path):
            if not target.exists():
                replace_file_atomic(target, json.dumps({"value": value}))
            seen.append(value)

    threads = [
        threading.Thread(target=publish, args=("first",)),
        threading.Thread(target=publish, args=("second",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert target.exists()
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["value"] in seen
    assert len(seen) == 2

