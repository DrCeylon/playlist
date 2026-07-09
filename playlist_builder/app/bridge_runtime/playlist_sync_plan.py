from __future__ import annotations

from typing import Any

from playlist_builder.app.playlist_sync.engine import PlaylistSyncEngine
from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.integration.gateway.registry import ProviderGatewayRegistry
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode
from playlist_builder.ui.shared.dto.playlist_library import (
    ManagedPlaylistDetail,
    ManagedPlaylistSummary,
    ManagedPlaylistTrack,
)
from playlist_builder.ui.shared.dto.playlist_sync import SyncDirection, SyncMode
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistSnapshot, RemotePlaylistTrack


def plan_sync(
    registry: ProviderGatewayRegistry,
    *,
    local_detail: ManagedPlaylistDetail,
    remote_snapshot: RemotePlaylistSnapshot | None,
    provider_id: ProviderId,
    direction: SyncDirection,
    sync_mode: SyncMode,
    remote_playlist_id: str | None = None,
) -> dict[str, Any]:
    """Build a sync plan without mutating any provider."""
    snapshot = remote_snapshot
    if snapshot is None:
        _ensure_provider_can_plan(registry, provider_id)
        if not remote_playlist_id:
            raise BridgeError(
                BridgeErrorCode.INVALID_REQUEST,
                "remote_playlist_id ou remote_snapshot est requis pour planifier une synchronisation.",
            )
        snapshot = _load_remote_snapshot(registry, provider_id, remote_playlist_id)
    else:
        _ensure_provider_registered(registry, provider_id)

    if snapshot.provider_id != provider_id:
        raise BridgeError(
            BridgeErrorCode.INVALID_REQUEST,
            "Le snapshot distant ne correspond pas au provider demandé.",
        )

    engine = PlaylistSyncEngine()
    plan = engine.build_plan(
        local=local_detail,
        remote=snapshot,
        direction=direction,
        sync_mode=sync_mode,
    )
    return {"sync_plan": plan.to_dict()}


def _ensure_provider_can_plan(registry: ProviderGatewayRegistry, provider_id: ProviderId) -> None:
    _ensure_provider_registered(registry, provider_id)
    gateway = registry.require(provider_id)
    if ProviderCapability.PLAYLIST_LIBRARY_BROWSE not in gateway.capabilities and ProviderCapability.PLAYLIST_SYNC not in gateway.capabilities:
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            f"Le fournisseur {provider_id.value} ne supporte pas la planification de sync.",
        )


def _ensure_provider_registered(registry: ProviderGatewayRegistry, provider_id: ProviderId) -> None:
    if registry.get(provider_id) is None:
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            f"Le fournisseur {provider_id.value} n'est pas disponible.",
        )


def _load_remote_snapshot(
    registry: ProviderGatewayRegistry,
    provider_id: ProviderId,
    remote_playlist_id: str,
) -> RemotePlaylistSnapshot:
    gateway = registry.require(provider_id)
    read_port = gateway.playlist_read
    if read_port is None:
        raise BridgeError(
            BridgeErrorCode.PROVIDER_UNAVAILABLE,
            f"Le port lecture playlist n'est pas configuré pour {provider_id.value}.",
        )
    return read_port.get_playlist(remote_playlist_id)


def managed_playlist_detail_from_dict(payload: dict[str, Any]) -> ManagedPlaylistDetail:
    summary_raw = payload.get("playlist") or payload
    if not isinstance(summary_raw, dict):
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "playlist invalide.")
    summary = ManagedPlaylistSummary(
        local_playlist_id=str(summary_raw.get("local_playlist_id", "")),
        name=str(summary_raw.get("name", "")),
        provider_id=ProviderId(str(summary_raw.get("provider_id", ProviderId.APPLE_MUSIC.value))),
        track_count=int(summary_raw.get("track_count", 0) or 0),
        sync_status=str(summary_raw.get("sync_status", "unknown")),
        last_synced_at_iso=str(summary_raw.get("last_synced_at_iso", "")),
        provider_playlist_id=str(summary_raw.get("provider_playlist_id", "")),
        source_kind=str(summary_raw.get("source_kind", "generated_import")),
        import_status=summary_raw.get("import_status"),
        history_session_id=str(summary_raw.get("history_session_id", "")),
    )
    tracks_raw = summary_raw.get("tracks", [])
    tracks: list[ManagedPlaylistTrack] = []
    if isinstance(tracks_raw, list):
        for item in tracks_raw:
            if not isinstance(item, dict):
                continue
            tracks.append(
                ManagedPlaylistTrack(
                    local_track_id=str(item.get("local_track_id", "")),
                    artist=str(item.get("artist", "")),
                    title=str(item.get("title", "")),
                    section=str(item.get("section", "")),
                    provider_track_id=str(item.get("provider_track_id", "")),
                    mapping_status=str(item.get("mapping_status", "matched")),
                )
            )
    return ManagedPlaylistDetail(summary=summary, tracks=tuple(tracks))


def remote_snapshot_from_dict(payload: dict[str, Any]) -> RemotePlaylistSnapshot:
    raw = payload.get("remote_playlist") or payload
    if not isinstance(raw, dict):
        raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "remote_playlist invalide.")
    tracks_raw = raw.get("tracks", [])
    tracks: list[RemotePlaylistTrack] = []
    if isinstance(tracks_raw, list):
        for item in tracks_raw:
            if not isinstance(item, dict):
                continue
            tracks.append(
                RemotePlaylistTrack(
                    remote_track_id=str(item.get("remote_track_id", "")),
                    artist=str(item.get("artist", "")),
                    title=str(item.get("title", "")),
                    album=str(item.get("album", "")),
                    duration_ms=int(item.get("duration_ms", 0) or 0),
                    position=int(item.get("position", 0) or 0),
                    provider_metadata=dict(item.get("provider_metadata", {}) or {}),
                )
            )
    return RemotePlaylistSnapshot(
        provider_id=ProviderId(str(raw.get("provider_id", ProviderId.APPLE_MUSIC.value))),
        remote_playlist_id=str(raw.get("remote_playlist_id", "")),
        name=str(raw.get("name", "")),
        snapshot_at_iso=str(raw.get("snapshot_at_iso", "")),
        tracks=tuple(tracks),
        track_count=int(raw.get("track_count", len(tracks)) or len(tracks)),
        checksum=str(raw.get("checksum", "")),
        source_kind=str(raw.get("source_kind", "provider_library")),
        source_url=str(raw.get("source_url", "")),
    )
