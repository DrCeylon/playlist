from __future__ import annotations

from playlist_builder.app.playlist_library.remote_link_resolver import (
    RemoteLinkStatus,
    RemotePlaylistLinkResult,
)
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.playlist_library import LinkedRemoteRef, ManagedPlaylistDetail


def existing_remote_playlist_id_for_provider(
    detail: ManagedPlaylistDetail | None,
    provider_id: ProviderId,
) -> str:
    """Return the persisted remote playlist ID for ``provider_id``, if any."""
    if detail is None:
        return ""
    summary = detail.summary
    if summary.provider_id == provider_id and summary.provider_playlist_id.strip():
        return summary.provider_playlist_id.strip()
    for ref in summary.linked_remote_refs:
        if ref.provider_id == provider_id and ref.remote_playlist_id.strip():
            return ref.remote_playlist_id.strip()
    return ""


def merge_linked_remote_refs(
    existing: ManagedPlaylistDetail | None,
    provider_id: ProviderId,
    link: RemotePlaylistLinkResult,
    checksum: str,
) -> tuple[LinkedRemoteRef, ...]:
    """Update the ref for ``provider_id`` while preserving all other provider links."""
    preserved = tuple(
        ref
        for ref in (existing.summary.linked_remote_refs if existing else ())
        if ref.provider_id != provider_id
    )
    if link.status == RemoteLinkStatus.LINKED and link.remote_playlist_id.strip():
        resolved_checksum = checksum or link.snapshot_checksum
        return preserved + (
            LinkedRemoteRef(
                provider_id=provider_id,
                remote_playlist_id=link.remote_playlist_id.strip(),
                snapshot_checksum=resolved_checksum,
                last_seen_snapshot_checksum=resolved_checksum,
                sync_state="linked",
            ),
        )
    if existing is not None:
        for ref in existing.summary.linked_remote_refs:
            if ref.provider_id == provider_id:
                return preserved + (ref,)
    return preserved


def resolve_provider_playlist_id(
    existing: ManagedPlaylistDetail | None,
    provider_id: ProviderId,
    primary_provider_id: ProviderId,
    link: RemotePlaylistLinkResult,
) -> str:
    """Legacy ``provider_playlist_id`` field — mirrors the primary provider link when linked."""
    if primary_provider_id != provider_id:
        return existing.summary.provider_playlist_id if existing else ""
    if link.status == RemoteLinkStatus.LINKED and link.remote_playlist_id.strip():
        return link.remote_playlist_id.strip()
    if existing is not None:
        return existing.summary.provider_playlist_id
    return ""
