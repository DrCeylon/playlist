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
