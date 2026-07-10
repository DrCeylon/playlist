from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.app.playlist_sync.comparison import PlaylistComparisonResult
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_library import LinkedRemoteRef, ManagedPlaylistDetail, PlaylistSyncConflict
from playlist_builder.ui.shared.dto.playlist_sync import PlaylistSyncAction, PlaylistSyncActionKind, SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot
from playlist_builder.ui.shared.dto.sync_conflict import (
    ConflictKind,
    ConflictScope,
    ConflictSeverity,
    recommended_resolution_for_kind,
)


@dataclass(frozen=True, slots=True)
class SyncConflictContext:
    """Provider-neutral context for conflict detection beyond track diff."""

    provider_id: ProviderId
    direction: SyncDirection
    sync_mode: SyncMode
    expected_local_playlist_version: int | None = None
    expected_remote_snapshot_checksum: str | None = None


def action_id(action: PlaylistSyncAction) -> str:
    return (
        f"{action.kind.value}:{action.track_key}:{action.local_track_id}:"
        f"{action.remote_track_id}:{action.source_position or 0}:{action.target_position or 0}"
    )


class PlaylistConflictDetector:
    """Detect provider-neutral sync conflicts from comparison, plan actions and context."""

    def detect(
        self,
        *,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
        comparison: PlaylistComparisonResult,
        actions: tuple[PlaylistSyncAction, ...],
        context: SyncConflictContext,
    ) -> tuple[PlaylistSyncConflict, ...]:
        conflicts: list[PlaylistSyncConflict] = []
        action_index = {action_id(action): action for action in actions}

        conflicts.extend(self._duplicate_conflicts(comparison))
        conflicts.extend(self._metadata_conflicts(comparison, context.sync_mode, action_index))
        conflicts.extend(self._rename_conflict(local, remote, context.sync_mode, actions))
        conflicts.extend(self._order_conflicts(comparison, actions, context))
        conflicts.extend(self._deletion_conflicts(actions, context))
        conflicts.extend(self._missing_track_conflicts(comparison, context))
        conflicts.extend(self._link_conflicts(local, remote, context))
        conflicts.extend(self._concurrent_modification_conflicts(local, remote, context))

        deduped = _dedupe_conflicts(conflicts)
        deduped.sort(key=lambda item: (item.scope, item.track_key, item.id))
        return tuple(deduped)

    def _duplicate_conflicts(self, comparison: PlaylistComparisonResult) -> list[PlaylistSyncConflict]:
        items: list[PlaylistSyncConflict] = []
        for key in comparison.local_duplicates:
            items.append(
                _conflict(
                    conflict_id=f"dup-local-{key}",
                    kind=ConflictKind.DUPLICATE_LOCAL,
                    track_key=key,
                    message="Doublon détecté dans la playlist locale",
                    severity=ConflictSeverity.BLOCKING,
                )
            )
        for key in comparison.remote_duplicates:
            items.append(
                _conflict(
                    conflict_id=f"dup-remote-{key}",
                    kind=ConflictKind.DUPLICATE_REMOTE,
                    track_key=key,
                    message="Doublon détecté dans la playlist distante",
                    severity=ConflictSeverity.BLOCKING,
                )
            )
        return items

    def _metadata_conflicts(
        self,
        comparison: PlaylistComparisonResult,
        sync_mode: SyncMode,
        action_index: dict[str, PlaylistSyncAction],
    ) -> list[PlaylistSyncConflict]:
        if sync_mode != SyncMode.MANUAL_RESOLVE:
            return []
        items: list[PlaylistSyncConflict] = []
        for mismatch in comparison.metadata_mismatches:
            related = tuple(
                aid
                for aid, action in action_index.items()
                if action.track_key == mismatch.track_key and action.kind == PlaylistSyncActionKind.MAP_TRACK
            )
            items.append(
                _conflict(
                    conflict_id=f"meta-{mismatch.track_key}",
                    kind=ConflictKind.METADATA_MISMATCH,
                    track_key=mismatch.track_key,
                    message=f"Écart métadonnées : {', '.join(mismatch.fields)}",
                    local_track_id=mismatch.local.local_track_id,
                    remote_track_id=mismatch.remote.remote_track_id,
                    affected_fields=mismatch.fields,
                    related_action_ids=related,
                    severity=ConflictSeverity.WARNING if "album" in mismatch.fields else ConflictSeverity.BLOCKING,
                )
            )
        return items

    def _rename_conflict(
        self,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
        sync_mode: SyncMode,
        actions: tuple[PlaylistSyncAction, ...],
    ) -> list[PlaylistSyncConflict]:
        if local.summary.name.strip() == remote.name.strip():
            return []
        related = tuple(aid for action in actions if action.kind == PlaylistSyncActionKind.RENAME_PLAYLIST for aid in (action_id(action),))
        if sync_mode == SyncMode.MANUAL_RESOLVE:
            return [
                _conflict(
                    conflict_id="rename-playlist",
                    kind=ConflictKind.RENAME_MISMATCH,
                    track_key="",
                    message=f"Nom différent : « {local.summary.name} » vs « {remote.name} »",
                    scope=ConflictScope.PLAYLIST,
                    related_action_ids=related,
                )
            ]
        return []

    def _order_conflicts(
        self,
        comparison: PlaylistComparisonResult,
        actions: tuple[PlaylistSyncAction, ...],
        context: SyncConflictContext,
    ) -> list[PlaylistSyncConflict]:
        if context.sync_mode != SyncMode.MANUAL_RESOLVE:
            return []
        items: list[PlaylistSyncConflict] = []
        for action in actions:
            if action.kind != PlaylistSyncActionKind.REORDER:
                continue
            items.append(
                _conflict(
                    conflict_id=f"order-{action.track_key}",
                    kind=ConflictKind.ORDER_MISMATCH,
                    track_key=action.track_key,
                    message=action.message or "Ordre différent entre local et distant",
                    local_position=action.target_position if context.direction == SyncDirection.PUSH_TO_PROVIDER else action.source_position,
                    remote_position=action.source_position if context.direction == SyncDirection.PUSH_TO_PROVIDER else action.target_position,
                    related_action_ids=(action_id(action),),
                    severity=ConflictSeverity.WARNING,
                )
            )
        return items

    def _deletion_conflicts(
        self,
        actions: tuple[PlaylistSyncAction, ...],
        context: SyncConflictContext,
    ) -> list[PlaylistSyncConflict]:
        if context.sync_mode != SyncMode.MANUAL_RESOLVE:
            return []
        items: list[PlaylistSyncConflict] = []
        for action in actions:
            if action.kind != PlaylistSyncActionKind.REMOVE_TRACK:
                continue
            kind = ConflictKind.DELETION_LOCAL if "local" in action.message.lower() else ConflictKind.DELETION_REMOTE
            items.append(
                _conflict(
                    conflict_id=f"delete-{action.track_key}-{kind.value}",
                    kind=kind,
                    track_key=action.track_key,
                    message=action.message,
                    local_track_id=action.local_track_id,
                    remote_track_id=action.remote_track_id,
                    related_action_ids=(action_id(action),),
                )
            )
        return items

    def _missing_track_conflicts(
        self,
        comparison: PlaylistComparisonResult,
        context: SyncConflictContext,
    ) -> list[PlaylistSyncConflict]:
        if context.sync_mode != SyncMode.MANUAL_RESOLVE:
            return []
        items: list[PlaylistSyncConflict] = []
        for track in comparison.only_remote:
            from playlist_builder.canonical.identity import track_identity_key

            key = track_identity_key(track.artist, track.title)
            items.append(
                _conflict(
                    conflict_id=f"missing-local-{key}",
                    kind=ConflictKind.MISSING_LOCAL,
                    track_key=key,
                    message=f"Présent uniquement côté distant : {track.artist} — {track.title}",
                    remote_track_id=track.remote_track_id,
                    remote_position=track.position,
                    severity=ConflictSeverity.INFO,
                )
            )
        for track in comparison.only_local:
            from playlist_builder.canonical.identity import track_identity_key

            key = track_identity_key(track.artist, track.title)
            items.append(
                _conflict(
                    conflict_id=f"missing-remote-{key}",
                    kind=ConflictKind.MISSING_REMOTE,
                    track_key=key,
                    message=f"Présent uniquement côté local : {track.artist} — {track.title}",
                    local_track_id=track.local_track_id,
                    severity=ConflictSeverity.INFO,
                )
            )
        return items

    def _link_conflicts(
        self,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
        context: SyncConflictContext,
    ) -> list[PlaylistSyncConflict]:
        if context.sync_mode not in {SyncMode.MANUAL_RESOLVE, SyncMode.MIRROR}:
            return []
        ref = _linked_ref(local, context.provider_id)
        if ref is None:
            return []
        if ref.remote_playlist_id and ref.remote_playlist_id != remote.remote_playlist_id:
            return [
                _conflict(
                    conflict_id=f"link-target-{context.provider_id.value}",
                    kind=ConflictKind.PROVIDER_LINK_MISMATCH,
                    track_key="",
                    message="La cible distante ne correspond pas à la liaison enregistrée.",
                    scope=ConflictScope.LINK,
                    severity=ConflictSeverity.BLOCKING,
                )
            ]
        return []

    def _concurrent_modification_conflicts(
        self,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
        context: SyncConflictContext,
    ) -> list[PlaylistSyncConflict]:
        items: list[PlaylistSyncConflict] = []
        ref = _linked_ref(local, context.provider_id)
        if ref is None:
            return items
        if ref.last_applied_snapshot_checksum and ref.last_applied_snapshot_checksum != remote.checksum:
            items.append(
                _conflict(
                    conflict_id="concurrent-remote",
                    kind=ConflictKind.CONCURRENT_MODIFICATION,
                    track_key="",
                    message="Le provider distant a changé depuis la dernière synchronisation appliquée.",
                    scope=ConflictScope.VERSION,
                    severity=ConflictSeverity.BLOCKING,
                )
            )
        if (
            context.expected_local_playlist_version is not None
            and local.summary.playlist_version != context.expected_local_playlist_version
        ):
            items.append(
                _conflict(
                    conflict_id="version-local-stale",
                    kind=ConflictKind.VERSION_LOCAL_STALE,
                    track_key="",
                    message="La playlist locale a changé depuis la prévisualisation.",
                    scope=ConflictScope.VERSION,
                    severity=ConflictSeverity.BLOCKING,
                )
            )
        if (
            context.expected_remote_snapshot_checksum is not None
            and remote.checksum != context.expected_remote_snapshot_checksum
        ):
            items.append(
                _conflict(
                    conflict_id="version-remote-stale",
                    kind=ConflictKind.VERSION_REMOTE_STALE,
                    track_key="",
                    message="Le snapshot distant a changé depuis la prévisualisation.",
                    scope=ConflictScope.VERSION,
                    severity=ConflictSeverity.BLOCKING,
                )
            )
        return items


def _linked_ref(local: ManagedPlaylistDetail, provider_id: ProviderId) -> LinkedRemoteRef | None:
    for ref in local.summary.linked_remote_refs:
        if ref.provider_id == provider_id:
            return ref
    return None


def _conflict(
    *,
    conflict_id: str,
    kind: ConflictKind,
    track_key: str,
    message: str,
    scope: ConflictScope = ConflictScope.TRACK,
    severity: ConflictSeverity = ConflictSeverity.BLOCKING,
    local_track_id: str = "",
    remote_track_id: str = "",
    local_position: int | None = None,
    remote_position: int | None = None,
    affected_fields: tuple[str, ...] = (),
    related_action_ids: tuple[str, ...] = (),
) -> PlaylistSyncConflict:
    return PlaylistSyncConflict(
        id=conflict_id,
        track_key=track_key,
        kind=kind.value,
        message=message,
        scope=scope.value,
        severity=severity.value,
        local_track_id=local_track_id,
        remote_track_id=remote_track_id,
        local_position=local_position,
        remote_position=remote_position,
        affected_fields=affected_fields,
        related_action_ids=related_action_ids,
        recommended_resolution=recommended_resolution_for_kind(kind.value),
    )


def _dedupe_conflicts(conflicts: list[PlaylistSyncConflict]) -> list[PlaylistSyncConflict]:
    seen: set[str] = set()
    unique: list[PlaylistSyncConflict] = []
    for conflict in conflicts:
        if conflict.id in seen:
            continue
        seen.add(conflict.id)
        unique.append(conflict)
    return unique
