from __future__ import annotations

import hashlib

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode


def sync_idempotency_key(
    *,
    local_playlist_id: str,
    provider_id: ProviderId,
    remote_playlist_id: str,
    direction: SyncDirection,
    sync_mode: SyncMode,
    plan_checksum: str,
    expected_local_playlist_version: int,
    expected_remote_snapshot_checksum: str,
) -> str:
    parts = [
        local_playlist_id.strip(),
        provider_id.value,
        remote_playlist_id.strip(),
        direction.value,
        sync_mode.value,
        plan_checksum.strip(),
        str(expected_local_playlist_version),
        expected_remote_snapshot_checksum.strip(),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:24]
