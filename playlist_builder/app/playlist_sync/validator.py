from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail
from playlist_builder.ui.shared.dto.playlist_sync import (
    PlaylistSyncAction,
    PlaylistSyncActionKind,
    PlaylistSyncPlan,
    SyncDirection,
    SyncMode,
)
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot


DESTRUCTIVE_ACTION_KINDS = frozenset(
    {
        PlaylistSyncActionKind.REMOVE_TRACK,
        PlaylistSyncActionKind.RENAME_PLAYLIST,
    }
)


@dataclass(frozen=True, slots=True)
class SyncApplyValidationResult:
    ok: bool
    error_code: str = ""
    message: str = ""
    requires_confirmation: bool = False
    destructive_actions: tuple[PlaylistSyncAction, ...] = ()
    executable_actions: tuple[PlaylistSyncAction, ...] = ()


class SyncApplyValidator:
    """Provider-neutral validation before applying a sync plan."""

    def validate(
        self,
        *,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
        plan: PlaylistSyncPlan,
        provider_id: ProviderId,
        direction: SyncDirection,
        sync_mode: SyncMode,
        confirm_destructive: bool,
        expected_local_playlist_version: int,
        expected_remote_snapshot_checksum: str,
        plan_checksum_expected: str,
        plan_checksum_actual: str,
        write_port: ProviderPlaylistWritePort | None,
        provider_capabilities: frozenset[ProviderCapability],
    ) -> SyncApplyValidationResult:
        if sync_mode == SyncMode.DRY_RUN:
            return _fail("invalid_sync_mode", "dry_run doit utiliser plan_sync, pas apply_sync.")

        if plan.local_playlist_id != local.summary.local_playlist_id:
            return _fail("playlist_mismatch", "Le plan ne correspond pas à la playlist locale.")

        if plan.target_provider_id != provider_id:
            return _fail("provider_mismatch", "Le plan ne correspond pas au provider demandé.")

        if plan.remote_playlist_id != remote.remote_playlist_id:
            return _fail("remote_playlist_mismatch", "Le plan ne correspond pas à la playlist distante.")

        if plan.direction != direction:
            return _fail("direction_mismatch", "La direction du plan ne correspond pas à la requête.")

        if plan.sync_mode != sync_mode:
            return _fail("sync_mode_mismatch", "Le mode de synchronisation ne correspond pas à la requête.")

        if plan_checksum_expected != plan_checksum_actual:
            return _fail("plan_checksum_mismatch", "Le checksum du plan est invalide ou obsolète.")

        if local.summary.playlist_version != expected_local_playlist_version:
            return _fail(
                "local_version_stale",
                "La playlist locale a changé depuis la prévisualisation. Recalculez le plan.",
            )

        if remote.checksum != expected_remote_snapshot_checksum:
            return _fail(
                "remote_snapshot_stale",
                "Le snapshot distant a changé depuis la prévisualisation. Recalculez le plan.",
            )

        if sync_mode == SyncMode.MANUAL_RESOLVE and plan.conflicts:
            return _fail(
                "blocked_conflict",
                "Des conflits subsistent. Résolvez-les avant d'appliquer la synchronisation.",
            )

        destructive = tuple(action for action in plan.actions if action.kind in DESTRUCTIVE_ACTION_KINDS)
        if sync_mode == SyncMode.APPEND_ONLY and destructive:
            return _fail(
                "append_only_destructive",
                "Le plan contient des actions destructives incompatibles avec append_only.",
            )

        if sync_mode == SyncMode.MIRROR and destructive and not confirm_destructive:
            return SyncApplyValidationResult(
                ok=False,
                error_code="confirmation_required",
                message="Confirmation requise pour appliquer des actions destructives.",
                requires_confirmation=True,
                destructive_actions=destructive,
            )

        if direction == SyncDirection.PUSH_TO_PROVIDER:
            if ProviderCapability.PLAYLIST_SYNC not in provider_capabilities:
                return _fail(
                    "provider_unavailable",
                    f"Le fournisseur {provider_id.value} ne supporte pas la synchronisation.",
                )
            if write_port is None:
                return _fail(
                    "write_port_missing",
                    f"Le port d'écriture playlist n'est pas configuré pour {provider_id.value}.",
                )

        executable = _filter_executable_actions(plan.actions, direction=direction, sync_mode=sync_mode)
        if not executable and not plan.conflicts:
            return SyncApplyValidationResult(ok=True, executable_actions=())

        unsupported = [
            action
            for action in plan.actions
            if action.kind not in {PlaylistSyncActionKind.ADD_TRACK}
            and action not in executable
        ]
        if unsupported and sync_mode != SyncMode.MIRROR:
            kinds = ", ".join(sorted({action.kind.value for action in unsupported}))
            return _fail("unsupported_actions", f"Actions non supportées en 6.5 : {kinds}.")

        return SyncApplyValidationResult(ok=True, destructive_actions=destructive, executable_actions=executable)


def _filter_executable_actions(
    actions: tuple[PlaylistSyncAction, ...],
    *,
    direction: SyncDirection,
    sync_mode: SyncMode,
) -> tuple[PlaylistSyncAction, ...]:
    allowed_kinds = {PlaylistSyncActionKind.ADD_TRACK}
    if sync_mode == SyncMode.MIRROR:
        allowed_kinds |= {PlaylistSyncActionKind.REMOVE_TRACK, PlaylistSyncActionKind.REORDER, PlaylistSyncActionKind.MAP_TRACK}
    filtered: list[PlaylistSyncAction] = []
    for action in actions:
        if action.kind not in allowed_kinds:
            continue
        if sync_mode == SyncMode.APPEND_ONLY and action.kind == PlaylistSyncActionKind.REMOVE_TRACK:
            continue
        filtered.append(action)
    return tuple(filtered)


def _fail(error_code: str, message: str) -> SyncApplyValidationResult:
    return SyncApplyValidationResult(ok=False, error_code=error_code, message=message)
