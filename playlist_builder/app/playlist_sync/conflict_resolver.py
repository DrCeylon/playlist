from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.app.playlist_sync.conflict_detector import action_id
from playlist_builder.ui.shared.dto.playlist_library import PlaylistSyncConflict
from playlist_builder.ui.shared.dto.playlist_sync import (
    PlaylistSyncAction,
    PlaylistSyncActionKind,
    PlaylistSyncPlan,
    PlaylistSyncSummary,
)
from playlist_builder.ui.shared.dto.sync_conflict import ConflictKind, ConflictResolutionStrategy


@dataclass(frozen=True, slots=True)
class ConflictResolution:
    conflict_id: str
    strategy: ConflictResolutionStrategy

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> ConflictResolution:
        strategy_raw = str(raw.get("strategy", "")).strip()
        try:
            strategy = ConflictResolutionStrategy(strategy_raw)
        except ValueError as exc:
            raise ValueError(f"stratégie de résolution invalide : {strategy_raw!r}") from exc
        conflict_id = str(raw.get("conflict_id", "")).strip()
        if not conflict_id:
            raise ValueError("conflict_id est requis.")
        return cls(conflict_id=conflict_id, strategy=strategy)


class PlaylistConflictResolver:
    """Apply user resolutions to a plan — never mutates playlists directly."""

    def resolve(
        self,
        plan: PlaylistSyncPlan,
        resolutions: tuple[ConflictResolution, ...],
    ) -> PlaylistSyncPlan:
        conflict_by_id = {conflict.id: conflict for conflict in plan.conflicts}
        resolution_map = {item.conflict_id: item.strategy for item in resolutions}

        unknown = [conflict_id for conflict_id in resolution_map if conflict_id not in conflict_by_id]
        if unknown:
            raise ValueError(f"Conflits inconnus : {', '.join(unknown)}")

        remaining_conflicts: list[PlaylistSyncConflict] = []
        actions = list(plan.actions)

        for conflict in plan.conflicts:
            strategy = resolution_map.get(conflict.id)
            if strategy is None:
                remaining_conflicts.append(conflict)
                continue
            if strategy == ConflictResolutionStrategy.DEFER:
                remaining_conflicts.append(conflict)
                continue
            actions = self._apply_resolution(actions, conflict, strategy)

        actions = self._dedupe_actions(actions)
        summary = _recompute_summary(plan.summary, actions=tuple(actions), conflicts=tuple(remaining_conflicts))
        return PlaylistSyncPlan(
            local_playlist_id=plan.local_playlist_id,
            target_provider_id=plan.target_provider_id,
            direction=plan.direction,
            sync_mode=plan.sync_mode,
            remote_playlist_id=plan.remote_playlist_id,
            actions=tuple(actions),
            conflicts=tuple(remaining_conflicts),
            summary=summary,
            playlist_name_local=plan.playlist_name_local,
            playlist_name_remote=plan.playlist_name_remote,
        )

    def _apply_resolution(
        self,
        actions: list[PlaylistSyncAction],
        conflict: PlaylistSyncConflict,
        strategy: ConflictResolutionStrategy,
    ) -> list[PlaylistSyncAction]:
        related_ids = set(conflict.related_action_ids)
        if strategy == ConflictResolutionStrategy.IGNORE:
            return [action for action in actions if action_id(action) not in related_ids and not _matches_conflict(action, conflict)]

        if strategy == ConflictResolutionStrategy.KEEP_LOCAL:
            return [
                action
                for action in actions
                if action_id(action) not in related_ids
                and not (
                    _matches_conflict(action, conflict)
                    and action.kind
                    in {
                        PlaylistSyncActionKind.ADD_TRACK,
                        PlaylistSyncActionKind.REMOVE_TRACK,
                        PlaylistSyncActionKind.REORDER,
                        PlaylistSyncActionKind.RENAME_PLAYLIST,
                    }
                )
            ]

        if strategy == ConflictResolutionStrategy.KEEP_REMOTE:
            return [
                action
                for action in actions
                if action_id(action) not in related_ids
                and not (_matches_conflict(action, conflict) and action.kind == PlaylistSyncActionKind.MAP_TRACK)
            ]

        if strategy == ConflictResolutionStrategy.MERGE:
            if conflict.kind != ConflictKind.METADATA_MISMATCH.value:
                return [action for action in actions if action_id(action) not in related_ids]
            merged = [action for action in actions if action_id(action) not in related_ids]
            merged.append(
                PlaylistSyncAction(
                    kind=PlaylistSyncActionKind.MAP_TRACK,
                    track_key=conflict.track_key,
                    artist="",
                    title="",
                    local_track_id=conflict.local_track_id,
                    remote_track_id=conflict.remote_track_id,
                    message="Fusion métadonnées après résolution",
                )
            )
            return merged

        return actions

    @staticmethod
    def _dedupe_actions(actions: list[PlaylistSyncAction]) -> list[PlaylistSyncAction]:
        seen: set[str] = set()
        unique: list[PlaylistSyncAction] = []
        for action in actions:
            aid = action_id(action)
            if aid in seen:
                continue
            seen.add(aid)
            unique.append(action)
        return unique


def _matches_conflict(action: PlaylistSyncAction, conflict: PlaylistSyncConflict) -> bool:
    if conflict.track_key and action.track_key == conflict.track_key:
        return True
    if conflict.scope == "playlist" and action.kind == PlaylistSyncActionKind.RENAME_PLAYLIST:
        return True
    return False


def _recompute_summary(
    previous: PlaylistSyncSummary,
    *,
    actions: tuple[PlaylistSyncAction, ...],
    conflicts: tuple[PlaylistSyncConflict, ...],
) -> PlaylistSyncSummary:
    additions = sum(1 for action in actions if action.kind == PlaylistSyncActionKind.ADD_TRACK)
    removals = sum(1 for action in actions if action.kind == PlaylistSyncActionKind.REMOVE_TRACK)
    reorders = sum(1 for action in actions if action.kind == PlaylistSyncActionKind.REORDER)
    metadata = sum(1 for action in actions if action.kind == PlaylistSyncActionKind.MAP_TRACK)
    rename_required = any(action.kind == PlaylistSyncActionKind.RENAME_PLAYLIST for action in actions)
    return PlaylistSyncSummary(
        additions=additions,
        removals=removals,
        already_present=previous.already_present,
        metadata_mismatches=metadata,
        reorders=reorders,
        conflicts=len(conflicts),
        rename_required=rename_required,
    )
