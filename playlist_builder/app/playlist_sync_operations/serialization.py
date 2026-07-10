from __future__ import annotations

from typing import Any

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_sync import (
    PlaylistSyncOperation,
    SyncActionOutcome,
    SyncDirection,
    SyncMode,
    SyncOperationStatus,
)

SCHEMA_VERSION = 1


def operation_from_dict(raw: dict[str, Any]) -> PlaylistSyncOperation:
    provider_raw = str(raw.get("provider_id", ProviderId.APPLE_MUSIC.value))
    try:
        provider_id = ProviderId(provider_raw)
    except ValueError:
        provider_id = ProviderId.APPLE_MUSIC
    direction_raw = str(raw.get("direction", SyncDirection.PUSH_TO_PROVIDER.value))
    try:
        direction = SyncDirection(direction_raw)
    except ValueError:
        direction = SyncDirection.PUSH_TO_PROVIDER
    mode_raw = str(raw.get("sync_mode", SyncMode.APPEND_ONLY.value))
    try:
        sync_mode = SyncMode(mode_raw)
    except ValueError:
        sync_mode = SyncMode.APPEND_ONLY
    status_raw = str(raw.get("status", SyncOperationStatus.PENDING.value))
    try:
        status = SyncOperationStatus(status_raw)
    except ValueError:
        status = SyncOperationStatus.PENDING
    return PlaylistSyncOperation(
        operation_id=str(raw.get("operation_id", "")),
        idempotency_key=str(raw.get("idempotency_key", "")),
        local_playlist_id=str(raw.get("local_playlist_id", "")),
        provider_id=provider_id,
        remote_playlist_id=str(raw.get("remote_playlist_id", "")),
        direction=direction,
        sync_mode=sync_mode,
        plan_checksum=str(raw.get("plan_checksum", "")),
        remote_snapshot_checksum=str(raw.get("remote_snapshot_checksum", "")),
        local_playlist_version_before=int(raw.get("local_playlist_version_before", 0) or 0),
        local_playlist_version_after=int(raw.get("local_playlist_version_after", 0) or 0),
        status=status,
        created_at_iso=str(raw.get("created_at_iso", "")),
        started_at_iso=str(raw.get("started_at_iso", "")),
        finished_at_iso=str(raw.get("finished_at_iso", "")),
        actions_total=int(raw.get("actions_total", 0) or 0),
        actions_completed=int(raw.get("actions_completed", 0) or 0),
        actions_failed=int(raw.get("actions_failed", 0) or 0),
        actions_skipped=int(raw.get("actions_skipped", 0) or 0),
        completed_actions=_outcomes_from_raw(raw.get("completed_actions")),
        failed_actions=_outcomes_from_raw(raw.get("failed_actions")),
        error_code=str(raw.get("error_code", "")),
        error_message=str(raw.get("error_message", "")),
    )


def operation_to_dict(operation: PlaylistSyncOperation) -> dict[str, Any]:
    return operation.to_dict()


def _outcomes_from_raw(raw: object) -> tuple[SyncActionOutcome, ...]:
    if not isinstance(raw, list):
        return ()
    outcomes: list[SyncActionOutcome] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        outcomes.append(
            SyncActionOutcome(
                action_id=str(item.get("action_id", "")),
                kind=str(item.get("kind", "")),
                track_key=str(item.get("track_key", "")),
                status=str(item.get("status", "")),
                message=str(item.get("message", "")),
            )
        )
    return tuple(outcomes)
