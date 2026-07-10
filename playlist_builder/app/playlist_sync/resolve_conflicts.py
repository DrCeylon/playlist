from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playlist_builder.app.playlist_sync.conflict_resolver import ConflictResolution, PlaylistConflictResolver
from playlist_builder.app.playlist_sync.engine import PlaylistSyncEngine
from playlist_builder.app.playlist_sync.plan_checksum import plan_checksum
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail
from playlist_builder.ui.shared.dto.playlist_sync import PlaylistSyncPlan, SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot


@dataclass(frozen=True, slots=True)
class ResolveSyncConflictsRequest:
    local_playlist_id: str
    provider_id: str
    direction: SyncDirection
    sync_mode: SyncMode
    remote_playlist_id: str
    resolutions: tuple[ConflictResolution, ...]


@dataclass(frozen=True, slots=True)
class ResolveSyncConflictsResult:
    plan: PlaylistSyncPlan
    plan_checksum: str
    remaining_conflicts: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sync_plan": self.plan.to_dict(),
            "plan_checksum": self.plan_checksum,
            "remaining_conflicts": self.remaining_conflicts,
            "message": self.message,
        }


class ResolveSyncConflicts:
    """Regenerate a plan after applying conflict resolutions — no repository mutation."""

    def __init__(
        self,
        *,
        engine: PlaylistSyncEngine | None = None,
        resolver: PlaylistConflictResolver | None = None,
    ) -> None:
        self._engine = engine or PlaylistSyncEngine()
        self._resolver = resolver or PlaylistConflictResolver()

    def execute(
        self,
        request: ResolveSyncConflictsRequest,
        *,
        local: ManagedPlaylistDetail,
        remote: RemotePlaylistSnapshot,
    ) -> ResolveSyncConflictsResult:
        if request.local_playlist_id != local.summary.local_playlist_id:
            raise ValueError("La playlist locale ne correspond pas à la requête.")
        if request.remote_playlist_id != remote.remote_playlist_id:
            raise ValueError("La playlist distante ne correspond pas à la requête.")

        baseline = self._engine.build_plan(
            local=local,
            remote=remote,
            direction=request.direction,
            sync_mode=request.sync_mode,
        )
        resolved = self._resolver.resolve(baseline, request.resolutions)
        remaining = len(resolved.conflicts)
        message = "Plan mis à jour après résolution des conflits."
        if remaining:
            message = f"{remaining} conflit(s) subsistent — résolution partielle."
        return ResolveSyncConflictsResult(
            plan=resolved,
            plan_checksum=plan_checksum(resolved),
            remaining_conflicts=remaining,
            message=message,
        )
