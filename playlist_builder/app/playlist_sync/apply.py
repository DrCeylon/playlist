from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import uuid4

from playlist_builder.app.playlist_library.repository import ManagedPlaylistRepository
from playlist_builder.app.playlist_sync.action_executor import SyncActionExecutor
from playlist_builder.app.playlist_sync.engine import PlaylistSyncEngine
from playlist_builder.app.playlist_sync.idempotency import sync_idempotency_key
from playlist_builder.app.playlist_sync.plan_checksum import plan_checksum
from playlist_builder.app.playlist_sync.state_updater import PlaylistSyncStateUpdater
from playlist_builder.app.playlist_sync.validator import SyncApplyValidator
from playlist_builder.app.playlist_sync_operations.repository import PlaylistSyncOperationRepository
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail
from playlist_builder.ui.shared.dto.playlist_sync import (
    ApplySyncResult,
    PlaylistSyncOperation,
    SyncActionOutcome,
    SyncDirection,
    SyncMode,
    SyncOperationStatus,
)
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot


@dataclass(frozen=True, slots=True)
class ApplySyncRequest:
    local_playlist_id: str
    provider_id: ProviderId
    direction: SyncDirection
    sync_mode: SyncMode
    confirm_destructive: bool
    expected_local_playlist_version: int
    expected_remote_snapshot_checksum: str
    plan_checksum: str
    remote_playlist_id: str = ""


class ApplySyncPlaylist:
    """Provider-neutral sync apply orchestrator."""

    def __init__(
        self,
        *,
        playlist_repository: ManagedPlaylistRepository,
        operation_repository: PlaylistSyncOperationRepository,
        validator: SyncApplyValidator | None = None,
        engine: PlaylistSyncEngine | None = None,
        executor: SyncActionExecutor | None = None,
        state_updater: PlaylistSyncStateUpdater | None = None,
    ) -> None:
        self._playlists = playlist_repository
        self._operations = operation_repository
        self._validator = validator or SyncApplyValidator()
        self._engine = engine or PlaylistSyncEngine()
        self._executor = executor or SyncActionExecutor()
        self._state_updater = state_updater or PlaylistSyncStateUpdater()

    def execute(
        self,
        request: ApplySyncRequest,
        *,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
        write_port: ProviderPlaylistWritePort | None = None,
        provider_capabilities: frozenset[ProviderCapability] | None = None,
    ) -> ApplySyncResult:
        capabilities = provider_capabilities or frozenset()
        regenerated = self._engine.build_plan(
            local=local,
            remote=remote,
            direction=request.direction,
            sync_mode=request.sync_mode,
        )
        checksum_actual = plan_checksum(regenerated)
        validation = self._validator.validate(
            local=local,
            remote=remote,
            plan=regenerated,
            provider_id=request.provider_id,
            direction=request.direction,
            sync_mode=request.sync_mode,
            confirm_destructive=request.confirm_destructive,
            expected_local_playlist_version=request.expected_local_playlist_version,
            expected_remote_snapshot_checksum=request.expected_remote_snapshot_checksum,
            plan_checksum_expected=request.plan_checksum,
            plan_checksum_actual=checksum_actual,
            write_port=write_port,
            provider_capabilities=capabilities,
        )
        if not validation.ok:
            operation = _blocked_operation(request, local, remote, checksum_actual, validation.error_code)
            self._operations.upsert(operation)
            return ApplySyncResult(
                operation=operation,
                final_sync_status=_blocked_status(validation.error_code),
                message=validation.message,
                requires_confirmation=validation.requires_confirmation,
                destructive_actions=validation.destructive_actions,
                conflicts=regenerated.conflicts,
            )

        idem_key = sync_idempotency_key(
            local_playlist_id=request.local_playlist_id,
            provider_id=request.provider_id,
            remote_playlist_id=remote.remote_playlist_id,
            direction=request.direction,
            sync_mode=request.sync_mode,
            plan_checksum=request.plan_checksum,
            expected_local_playlist_version=request.expected_local_playlist_version,
            expected_remote_snapshot_checksum=request.expected_remote_snapshot_checksum,
        )
        existing = self._operations.get_by_idempotency_key(idem_key)
        if existing is not None and existing.status in {SyncOperationStatus.COMPLETED, SyncOperationStatus.NO_OP}:
            current = self._playlists.get_playlist(request.local_playlist_id) or local
            return _result_from_existing(existing, current, "Synchronisation déjà appliquée (idempotent).")
        if existing is not None and existing.status == SyncOperationStatus.RUNNING:
            return ApplySyncResult(
                operation=existing,
                final_sync_status="pending",
                message="Une synchronisation identique est déjà en cours.",
            )

        if not validation.executable_actions:
            operation = _finalize_operation(
                _base_operation(request, local, remote, checksum_actual, idem_key),
                status=SyncOperationStatus.NO_OP,
                completed=(),
                failed=(),
                skipped=(),
            )
            self._operations.upsert(operation)
            updated = self._state_updater.apply_no_op(
                local,
                provider_id=request.provider_id,
                remote_playlist_id=remote.remote_playlist_id,
            )
            self._playlists.upsert(updated)
            return ApplySyncResult(
                operation=operation,
                final_sync_status="synced",
                message="Aucune action à appliquer.",
                updated_playlist=updated.to_dict(),
            )

        now = datetime.now().isoformat(timespec="seconds")
        operation = replace(
            _base_operation(request, local, remote, checksum_actual, idem_key),
            status=SyncOperationStatus.RUNNING,
            started_at_iso=now,
            actions_total=len(validation.executable_actions),
        )
        self._operations.upsert(operation)

        completed: list[SyncActionOutcome] = []
        failed: list[SyncActionOutcome] = []
        skipped: list[SyncActionOutcome] = []
        working = local
        local_changed = False

        for index, action in enumerate(validation.executable_actions):
            action_id = f"{operation.operation_id}-a{index}"
            if request.direction == SyncDirection.PULL_FROM_PROVIDER:
                if action.kind.value != "add_track":
                    skipped.append(
                        SyncActionOutcome(
                            action_id=action_id,
                            kind=action.kind.value,
                            track_key=action.track_key,
                            status="skipped",
                            message="Action pull non supportée en 6.5.",
                        )
                    )
                    continue
                track = self._executor.pull_track_from_action(
                    action,
                    local_playlist_id=local.summary.local_playlist_id,
                    index=index,
                )
                working = self._state_updater.apply_pull_tracks(working, (track,))
                local_changed = True
                completed.append(
                    SyncActionOutcome(
                        action_id=action_id,
                        kind=action.kind.value,
                        track_key=action.track_key,
                        status="completed",
                        message="Morceau ajouté localement.",
                    )
                )
                continue

            if write_port is None:
                outcome = SyncActionOutcome(
                    action_id=action_id,
                    kind=action.kind.value,
                    track_key=action.track_key,
                    status="failed",
                    message="Write port indisponible.",
                )
                failed.append(outcome)
                break

            outcome = self._executor.execute_push(
                action,
                write_port=write_port,
                remote_playlist_id=remote.remote_playlist_id,
                action_id=action_id,
            )
            if outcome.status == "completed":
                completed.append(outcome)
            elif outcome.status == "skipped":
                skipped.append(outcome)
            else:
                failed.append(outcome)
                break

        if failed:
            status = SyncOperationStatus.PARTIAL if completed else SyncOperationStatus.FAILED
            final_sync = "partial" if completed else "error"
            working = self._state_updater.apply_partial(
                working,
                provider_id=request.provider_id,
                remote_playlist_id=remote.remote_playlist_id,
                remote_snapshot_checksum=remote.checksum,
            )
        else:
            status = SyncOperationStatus.COMPLETED
            final_sync = "synced"
            working = self._state_updater.apply_success(
                working,
                provider_id=request.provider_id,
                remote_playlist_id=remote.remote_playlist_id,
                remote_snapshot_checksum=remote.checksum,
                sync_status=final_sync,
                local_content_changed=local_changed,
            )

        self._playlists.upsert(working)
        operation = _finalize_operation(
            operation,
            status=status,
            completed=tuple(completed),
            failed=tuple(failed),
            skipped=tuple(skipped),
            local_version_after=working.summary.playlist_version,
        )
        self._operations.upsert(operation)

        message = "Synchronisation appliquée avec succès."
        if status == SyncOperationStatus.PARTIAL:
            message = "Synchronisation partiellement appliquée."
        elif status == SyncOperationStatus.FAILED:
            message = failed[0].message if failed else "Échec de la synchronisation."

        return ApplySyncResult(
            operation=operation,
            final_sync_status=final_sync,
            message=message,
            actions_applied=tuple(completed),
            actions_failed=tuple(failed),
            actions_skipped=tuple(skipped),
            updated_playlist=working.to_dict(),
            remote_snapshot_checksum_after=remote.checksum,
        )


def _base_operation(
    request: ApplySyncRequest,
    local: ManagedPlaylistDetail,
    remote: RemotePlaylistSnapshot,
    checksum_actual: str,
    idem_key: str,
) -> PlaylistSyncOperation:
    now = datetime.now().isoformat(timespec="seconds")
    return PlaylistSyncOperation(
        operation_id=f"syncop-{uuid4()}",
        idempotency_key=idem_key,
        local_playlist_id=request.local_playlist_id,
        provider_id=request.provider_id,
        remote_playlist_id=remote.remote_playlist_id,
        direction=request.direction,
        sync_mode=request.sync_mode,
        plan_checksum=checksum_actual,
        remote_snapshot_checksum=remote.checksum,
        local_playlist_version_before=local.summary.playlist_version,
        local_playlist_version_after=local.summary.playlist_version,
        status=SyncOperationStatus.PENDING,
        created_at_iso=now,
    )


def _blocked_operation(
    request: ApplySyncRequest,
    local: ManagedPlaylistDetail,
    remote: RemotePlaylistSnapshot,
    checksum_actual: str,
    error_code: str,
) -> PlaylistSyncOperation:
    if error_code == "blocked_conflict":
        status = SyncOperationStatus.BLOCKED_CONFLICT
    elif error_code == "confirmation_required":
        status = SyncOperationStatus.BLOCKED_CONFIRMATION
    else:
        status = SyncOperationStatus.FAILED
    return replace(
        _base_operation(request, local, remote, checksum_actual, f"blocked-{uuid4()}"),
        status=status,
        error_code=error_code,
        finished_at_iso=datetime.now().isoformat(timespec="seconds"),
    )


def _finalize_operation(
    operation: PlaylistSyncOperation,
    *,
    status: SyncOperationStatus,
    completed: tuple[SyncActionOutcome, ...],
    failed: tuple[SyncActionOutcome, ...],
    skipped: tuple[SyncActionOutcome, ...],
    local_version_after: int | None = None,
) -> PlaylistSyncOperation:
    return replace(
        operation,
        status=status,
        finished_at_iso=datetime.now().isoformat(timespec="seconds"),
        actions_completed=len(completed),
        actions_failed=len(failed),
        actions_skipped=len(skipped),
        completed_actions=completed,
        failed_actions=failed,
        local_playlist_version_after=local_version_after or operation.local_playlist_version_after,
    )


def _result_from_existing(
    operation: PlaylistSyncOperation,
    local: ManagedPlaylistDetail,
    message: str,
) -> ApplySyncResult:
    return ApplySyncResult(
        operation=operation,
        final_sync_status=local.summary.sync_status,
        message=message,
        actions_applied=operation.completed_actions,
        actions_failed=operation.failed_actions,
        updated_playlist=local.to_dict(),
        remote_snapshot_checksum_after=operation.remote_snapshot_checksum,
    )


def _blocked_status(error_code: str) -> str:
    if error_code == "confirmation_required":
        return "pending"
    if error_code == "blocked_conflict":
        return "conflict"
    return "error"
