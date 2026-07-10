from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_library import PlaylistSyncConflict
from playlist_builder.ui.shared.validation import dto_to_dict


class SyncMode(StrEnum):
    """Playlist sync behaviour when applying a plan (dry_run never mutates providers)."""

    DRY_RUN = "dry_run"
    APPEND_ONLY = "append_only"
    MIRROR = "mirror"
    MANUAL_RESOLVE = "manual_resolve"


class SyncDirection(StrEnum):
    PULL_FROM_PROVIDER = "pull_from_provider"
    PUSH_TO_PROVIDER = "push_to_provider"
    BIDIRECTIONAL_PREVIEW = "bidirectional_preview"


class PlaylistSyncActionKind(StrEnum):
    ADD_TRACK = "add_track"
    REMOVE_TRACK = "remove_track"
    REORDER = "reorder"
    MAP_TRACK = "map_track"
    RENAME_PLAYLIST = "rename_playlist"


@dataclass(frozen=True, slots=True)
class PlaylistSyncAction:
    kind: PlaylistSyncActionKind
    track_key: str
    artist: str
    title: str
    message: str = ""
    local_track_id: str = ""
    remote_track_id: str = ""
    source_position: int | None = None
    target_position: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = dto_to_dict(self)
        payload["kind"] = self.kind.value
        return payload


@dataclass(frozen=True, slots=True)
class PlaylistSyncSummary:
    additions: int = 0
    removals: int = 0
    already_present: int = 0
    metadata_mismatches: int = 0
    reorders: int = 0
    conflicts: int = 0
    rename_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dto_to_dict(self)


@dataclass(frozen=True, slots=True)
class PlaylistSyncPlan:
    local_playlist_id: str
    target_provider_id: ProviderId
    direction: SyncDirection
    sync_mode: SyncMode
    remote_playlist_id: str
    actions: tuple[PlaylistSyncAction, ...]
    conflicts: tuple[PlaylistSyncConflict, ...]
    summary: PlaylistSyncSummary
    playlist_name_local: str = ""
    playlist_name_remote: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_playlist_id": self.local_playlist_id,
            "target_provider_id": self.target_provider_id.value,
            "direction": self.direction.value,
            "sync_mode": self.sync_mode.value,
            "remote_playlist_id": self.remote_playlist_id,
            "playlist_name_local": self.playlist_name_local,
            "playlist_name_remote": self.playlist_name_remote,
            "actions": [action.to_dict() for action in self.actions],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "summary": self.summary.to_dict(),
        }


class SyncOperationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED_CONFIRMATION = "blocked_confirmation"
    BLOCKED_CONFLICT = "blocked_conflict"
    NO_OP = "no_op"


@dataclass(frozen=True, slots=True)
class SyncActionOutcome:
    action_id: str
    kind: str
    track_key: str
    status: str
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dto_to_dict(self)


@dataclass(frozen=True, slots=True)
class PlaylistSyncOperation:
    operation_id: str
    idempotency_key: str
    local_playlist_id: str
    provider_id: ProviderId
    remote_playlist_id: str
    direction: SyncDirection
    sync_mode: SyncMode
    plan_checksum: str
    remote_snapshot_checksum: str
    local_playlist_version_before: int
    local_playlist_version_after: int
    status: SyncOperationStatus
    created_at_iso: str
    started_at_iso: str = ""
    finished_at_iso: str = ""
    actions_total: int = 0
    actions_completed: int = 0
    actions_failed: int = 0
    actions_skipped: int = 0
    completed_actions: tuple[SyncActionOutcome, ...] = ()
    failed_actions: tuple[SyncActionOutcome, ...] = ()
    error_code: str = ""
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "operation_id": self.operation_id,
            "idempotency_key": self.idempotency_key,
            "local_playlist_id": self.local_playlist_id,
            "provider_id": self.provider_id.value,
            "remote_playlist_id": self.remote_playlist_id,
            "direction": self.direction.value,
            "sync_mode": self.sync_mode.value,
            "plan_checksum": self.plan_checksum,
            "remote_snapshot_checksum": self.remote_snapshot_checksum,
            "local_playlist_version_before": self.local_playlist_version_before,
            "local_playlist_version_after": self.local_playlist_version_after,
            "status": self.status.value,
            "created_at_iso": self.created_at_iso,
            "started_at_iso": self.started_at_iso,
            "finished_at_iso": self.finished_at_iso,
            "actions_total": self.actions_total,
            "actions_completed": self.actions_completed,
            "actions_failed": self.actions_failed,
            "actions_skipped": self.actions_skipped,
            "completed_actions": [item.to_dict() for item in self.completed_actions],
            "failed_actions": [item.to_dict() for item in self.failed_actions],
            "error_code": self.error_code,
            "error_message": self.error_message,
        }
        return payload


@dataclass(frozen=True, slots=True)
class ApplySyncResult:
    operation: PlaylistSyncOperation
    final_sync_status: str
    message: str
    actions_applied: tuple[SyncActionOutcome, ...] = ()
    actions_failed: tuple[SyncActionOutcome, ...] = ()
    actions_skipped: tuple[SyncActionOutcome, ...] = ()
    updated_playlist: dict[str, Any] | None = None
    requires_confirmation: bool = False
    destructive_actions: tuple[PlaylistSyncAction, ...] = ()
    conflicts: tuple[PlaylistSyncConflict, ...] = ()
    remote_snapshot_checksum_after: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "operation": self.operation.to_dict(),
            "final_sync_status": self.final_sync_status,
            "message": self.message,
            "actions_applied": [item.to_dict() for item in self.actions_applied],
            "actions_failed": [item.to_dict() for item in self.actions_failed],
            "actions_skipped": [item.to_dict() for item in self.actions_skipped],
            "provider_id": self.operation.provider_id.value,
            "remote_playlist_id": self.operation.remote_playlist_id,
            "local_playlist_version_before": self.operation.local_playlist_version_before,
            "local_playlist_version_after": self.operation.local_playlist_version_after,
            "requires_confirmation": self.requires_confirmation,
            "destructive_actions": [action.to_dict() for action in self.destructive_actions],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "remote_snapshot_checksum_before": self.operation.remote_snapshot_checksum,
            "remote_snapshot_checksum_after": self.remote_snapshot_checksum_after,
        }
        if self.updated_playlist is not None:
            payload["updated_playlist"] = self.updated_playlist
        return payload
