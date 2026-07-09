from __future__ import annotations

import ast
from pathlib import Path

import pytest

from playlist_builder.app.playlist_sync.comparison import PlaylistComparisonService
from playlist_builder.app.playlist_sync.engine import PlaylistSyncEngine
from playlist_builder.app.playlist_sync.planner import PlaylistSyncPlanner
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_library import ManagedPlaylistDetail, ManagedPlaylistSummary, ManagedPlaylistTrack
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack, remote_playlist_snapshot_checksum


def _summary(**overrides: object) -> ManagedPlaylistSummary:
    base = dict(
        local_playlist_id="local-1",
        name="Workout",
        provider_id=ProviderId.APPLE_MUSIC,
        track_count=2,
        sync_status="pending",
    )
    base.update(overrides)
    return ManagedPlaylistSummary(**base)


def _local_track(artist: str, title: str, **kwargs: object) -> ManagedPlaylistTrack:
    return ManagedPlaylistTrack(
        local_track_id=str(kwargs.get("local_track_id", f"loc-{artist}-{title}")),
        artist=artist,
        title=title,
        provider_track_id=str(kwargs.get("provider_track_id", "")),
    )


def _remote_track(artist: str, title: str, position: int, **kwargs: object) -> RemotePlaylistTrack:
    return RemotePlaylistTrack(
        remote_track_id=str(kwargs.get("remote_track_id", f"rem-{artist}-{title}")),
        artist=artist,
        title=title,
        album=str(kwargs.get("album", "")),
        position=position,
    )


def _local_detail(tracks: tuple[ManagedPlaylistTrack, ...], **summary_overrides: object) -> ManagedPlaylistDetail:
    summary = _summary(track_count=len(tracks), **summary_overrides)
    return ManagedPlaylistDetail(summary=summary, tracks=tracks)


def _remote_snapshot(tracks: tuple[RemotePlaylistTrack, ...], **overrides: object) -> RemotePlaylistSnapshot:
    checksum = remote_playlist_snapshot_checksum(tracks)
    base = dict(
        provider_id=ProviderId.APPLE_MUSIC,
        remote_playlist_id="remote-1",
        name="Workout",
        snapshot_at_iso="2026-07-09T12:00:00Z",
        tracks=tracks,
        track_count=len(tracks),
        checksum=checksum,
        source_kind="provider_library",
    )
    base.update(overrides)
    return RemotePlaylistSnapshot(**base)


def test_comparison_identical_playlists() -> None:
    local = _local_detail((_local_track("Kygo", "Firestone"), _local_track("Avicii", "Levels")))
    remote = _remote_snapshot(
        (
            _remote_track("Kygo", "Firestone", 1),
            _remote_track("Avicii", "Levels", 2),
        )
    )
    result = PlaylistComparisonService().compare(local.tracks, remote.tracks)
    assert len(result.matched) == 2
    assert result.only_local == ()
    assert result.only_remote == ()


def test_comparison_divergent_playlists() -> None:
    local = _local_detail((_local_track("Kygo", "Firestone"),))
    remote = _remote_snapshot((_remote_track("Kygo", "Firestone", 1), _remote_track("Daft Punk", "One More Time", 2)))
    result = PlaylistComparisonService().compare(local.tracks, remote.tracks)
    assert len(result.matched) == 1
    assert len(result.only_remote) == 1
    assert result.only_remote[0].title == "One More Time"


def test_comparison_empty_playlists() -> None:
    result = PlaylistComparisonService().compare((), ())
    assert result.matched == ()
    assert result.only_local == ()
    assert result.only_remote == ()


def test_engine_dry_run_pull_additions() -> None:
    local = _local_detail(())
    remote = _remote_snapshot((_remote_track("Kygo", "Firestone", 1),))
    plan = PlaylistSyncEngine().dry_run(local=local, remote=remote, direction=SyncDirection.PULL_FROM_PROVIDER)
    assert plan.sync_mode == SyncMode.DRY_RUN
    assert plan.summary.additions == 1
    assert plan.summary.removals == 0
    assert plan.summary.already_present == 0
    assert any(action.kind.value == "add_track" for action in plan.actions)


def test_engine_dry_run_mirror_removes_missing_locally() -> None:
    local = _local_detail((_local_track("Only", "Local"),))
    remote = _remote_snapshot(())
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.DRY_RUN,
    )
    assert plan.summary.removals == 1


def test_engine_append_only_skips_removals() -> None:
    local = _local_detail((_local_track("Only", "Local"),))
    remote = _remote_snapshot((_remote_track("New", "Remote", 1),))
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.APPEND_ONLY,
    )
    assert plan.summary.additions == 1
    assert plan.summary.removals == 0


def test_engine_manual_resolve_metadata_conflict() -> None:
    local = _local_detail((_local_track("Kygo", "Firestone", provider_track_id="old-id"),))
    remote = _remote_snapshot((_remote_track("Kygo", "Firestone", 1, remote_track_id="new-id", album="Album"),))
    plan = PlaylistSyncEngine().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.MANUAL_RESOLVE,
    )
    assert plan.summary.conflicts >= 1
    assert not any(action.kind.value == "map_track" for action in plan.actions)


def test_engine_rename_action_when_names_differ() -> None:
    local = _local_detail((), name="Local Name")
    remote = _remote_snapshot((), name="Remote Name")
    plan = PlaylistSyncEngine().dry_run(local=local, remote=remote, direction=SyncDirection.PULL_FROM_PROVIDER)
    assert plan.summary.rename_required is True
    assert any(action.kind.value == "rename_playlist" for action in plan.actions)


def test_dry_run_is_deterministic() -> None:
    local = _local_detail(
        (
            _local_track("A", "One"),
            _local_track("B", "Two"),
        )
    )
    remote = _remote_snapshot(
        (
            _remote_track("A", "One", 1),
            _remote_track("C", "Three", 2),
        )
    )
    engine = PlaylistSyncEngine()
    first = engine.dry_run(local=local, remote=remote, direction=SyncDirection.PULL_FROM_PROVIDER)
    second = engine.dry_run(local=local, remote=remote, direction=SyncDirection.PULL_FROM_PROVIDER)
    assert first.to_dict() == second.to_dict()


def test_planner_duplicate_conflict() -> None:
    local = _local_detail(
        (
            _local_track("Dup", "Song", local_track_id="1"),
            _local_track("Dup", "Song", local_track_id="2"),
        )
    )
    remote = _remote_snapshot(())
    plan = PlaylistSyncPlanner().build_plan(
        local=local,
        remote=remote,
        direction=SyncDirection.PULL_FROM_PROVIDER,
        sync_mode=SyncMode.DRY_RUN,
        comparison=PlaylistComparisonService().compare(local.tracks, remote.tracks),
    )
    assert plan.summary.conflicts >= 1


def test_playlist_sync_module_has_no_apple_imports() -> None:
    root = Path(__file__).resolve().parents[1] / "playlist_builder" / "app" / "playlist_sync"
    forbidden = ("apple_music", "integration.apple")
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(token in alias.name for token in forbidden):
                        offenders.append(f"{path.name}: {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if any(token in node.module for token in forbidden):
                    offenders.append(f"{path.name}: {node.module}")
    assert offenders == []
