from __future__ import annotations

from datetime import datetime

from playlist_builder.app.playlist_library.remote_link_resolver import (
    ProviderRemotePlaylistLinker,
    RemoteLinkStatus,
    RemotePlaylistLinkResult,
)
from playlist_builder.app.playlist_library.repository import ManagedPlaylistRepository
from playlist_builder.app.playlist_library.snapshot_archive import SnapshotArchive
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.ui.shared.dto.enums import ImportPhase, ImportTrackStatus
from playlist_builder.ui.shared.dto.import_state import ImportResultState, ImportTrackOutcome
from playlist_builder.ui.shared.dto.playlist_library import (
    LinkedRemoteRef,
    ManagedPlaylistDetail,
    ManagedPlaylistSummary,
    ManagedPlaylistTrack,
    PlaylistOrigin,
)


_TERMINAL_PHASES = frozenset({ImportPhase.COMPLETED, ImportPhase.PARTIAL_SUCCESS})


class RegisterGeneratedImport:
    """Persist a generated import as a managed playlist with optional provider link."""

    def __init__(
        self,
        repository: ManagedPlaylistRepository,
        snapshots: SnapshotArchive,
        *,
        linker: ProviderRemotePlaylistLinker | None = None,
    ) -> None:
        self._repository = repository
        self._snapshots = snapshots
        self._linker = linker or ProviderRemotePlaylistLinker()

    def execute(
        self,
        *,
        history_session_id: str,
        provider_id: ProviderId,
        playlist_name: str,
        import_result: ImportResultState,
        read_port: ProviderPlaylistReadPort | None = None,
    ) -> ManagedPlaylistDetail | None:
        session_id = history_session_id.strip()
        if not session_id or import_result.phase not in _TERMINAL_PHASES:
            return None

        local_playlist_id = f"hist-{session_id}"
        existing = self._repository.get_playlist(local_playlist_id)
        existing_remote_id = _existing_remote_playlist_id(existing)
        link = self._linker.resolve(
            read_port,
            provider_id=provider_id,
            playlist_name=playlist_name,
            existing_remote_id=existing_remote_id,
        )
        checksum = self._store_remote_snapshot(read_port, link)
        tracks = _tracks_from_import_result(import_result, local_playlist_id)
        now = datetime.now().isoformat(timespec="seconds")
        version = (existing.summary.playlist_version if existing else 0) + 1
        created_at = existing.summary.created_at_iso if existing and existing.summary.created_at_iso else now
        linked_refs = _linked_remote_refs(provider_id, link, checksum)
        provider_playlist_id = link.remote_playlist_id if link.status == RemoteLinkStatus.LINKED else ""

        summary = ManagedPlaylistSummary(
            local_playlist_id=local_playlist_id,
            name=playlist_name.strip() or import_result.playlist_name,
            provider_id=provider_id,
            track_count=len(tracks),
            sync_status=_sync_status(import_result.phase, link),
            last_synced_at_iso=now if link.status == RemoteLinkStatus.LINKED else (existing.summary.last_synced_at_iso if existing else ""),
            provider_playlist_id=provider_playlist_id,
            source_kind="generated_import",
            import_status=import_result.phase.value,
            history_session_id=session_id,
            origin=PlaylistOrigin.GENERATED.value,
            playlist_version=version,
            linked_remote_refs=linked_refs,
            created_at_iso=created_at,
            updated_at_iso=now,
        )
        detail = ManagedPlaylistDetail(summary=summary, tracks=tracks)
        return self._repository.upsert(detail)

    def _store_remote_snapshot(
        self,
        read_port: ProviderPlaylistReadPort | None,
        link: RemotePlaylistLinkResult,
    ) -> str:
        if link.status != RemoteLinkStatus.LINKED or not link.remote_playlist_id or read_port is None:
            return link.snapshot_checksum
        try:
            snapshot = read_port.get_playlist(link.remote_playlist_id)
            self._snapshots.store(snapshot)
            return snapshot.checksum
        except (OSError, RuntimeError, ValueError):
            return link.snapshot_checksum


def _existing_remote_playlist_id(detail: ManagedPlaylistDetail | None) -> str:
    if detail is None:
        return ""
    if detail.summary.provider_playlist_id.strip():
        return detail.summary.provider_playlist_id.strip()
    if detail.summary.linked_remote_refs:
        return detail.summary.linked_remote_refs[0].remote_playlist_id.strip()
    return ""


def _tracks_from_import_result(
    import_result: ImportResultState,
    local_playlist_id: str,
) -> tuple[ManagedPlaylistTrack, ...]:
    tracks: list[ManagedPlaylistTrack] = []
    for index, outcome in enumerate(import_result.outcomes):
        track = _track_from_outcome(outcome, local_playlist_id, index)
        if track is not None:
            tracks.append(track)
    return tuple(tracks)


def _track_from_outcome(
    outcome: ImportTrackOutcome,
    local_playlist_id: str,
    index: int,
) -> ManagedPlaylistTrack | None:
    artist = outcome.artist.strip()
    title = outcome.title.strip()
    if not artist or not title:
        return None
    status = outcome.status
    if status == ImportTrackStatus.ADDED:
        mapping = "matched"
    elif status == ImportTrackStatus.NOT_FOUND:
        mapping = "missing_on_provider"
    elif status == ImportTrackStatus.SKIPPED:
        mapping = "matched"
    else:
        mapping = "unresolved"
    return ManagedPlaylistTrack(
        local_track_id=f"{local_playlist_id}-tr-{index}",
        artist=artist,
        title=title,
        section=outcome.section,
        mapping_status=mapping,
    )


def _linked_remote_refs(
    provider_id: ProviderId,
    link: RemotePlaylistLinkResult,
    checksum: str,
) -> tuple[LinkedRemoteRef, ...]:
    if link.status != RemoteLinkStatus.LINKED or not link.remote_playlist_id:
        return ()
    resolved_checksum = checksum or link.snapshot_checksum
    return (
        LinkedRemoteRef(
            provider_id=provider_id,
            remote_playlist_id=link.remote_playlist_id,
            snapshot_checksum=resolved_checksum,
            last_seen_snapshot_checksum=resolved_checksum,
            sync_state="linked",
        ),
    )


def _sync_status(phase: ImportPhase, link: RemotePlaylistLinkResult) -> str:
    if link.status == RemoteLinkStatus.AMBIGUOUS:
        return "not_linked"
    if link.status != RemoteLinkStatus.LINKED:
        return "not_linked"
    if phase == ImportPhase.PARTIAL_SUCCESS:
        return "partial"
    return "synced"
