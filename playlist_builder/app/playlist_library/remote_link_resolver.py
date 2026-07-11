from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort


class RemoteLinkStatus(StrEnum):
    LINKED = "linked"
    UNLINKED = "unlinked"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class RemotePlaylistLinkResult:
    status: RemoteLinkStatus
    remote_playlist_id: str = ""
    snapshot_checksum: str = ""
    message: str = ""


class ProviderRemotePlaylistLinker:
    """Resolve a provider playlist ID without inventing identifiers or guessing on ambiguity."""

    def resolve(
        self,
        read_port: ProviderPlaylistReadPort | None,
        *,
        provider_id: ProviderId,
        playlist_name: str,
        existing_remote_id: str = "",
    ) -> RemotePlaylistLinkResult:
        del provider_id
        existing = existing_remote_id.strip()
        if existing:
            return self._resolve_existing(read_port, existing)

        if read_port is None:
            return RemotePlaylistLinkResult(
                status=RemoteLinkStatus.UNLINKED,
                message="Lecture provider indisponible pour lier la playlist distante.",
            )

        name = playlist_name.strip()
        if not name:
            return RemotePlaylistLinkResult(
                status=RemoteLinkStatus.UNLINKED,
                message="Nom de playlist manquant pour lier la playlist distante.",
            )

        try:
            matches = [item for item in read_port.list_playlists() if item.name == name]
        except (OSError, RuntimeError, ValueError):
            return RemotePlaylistLinkResult(
                status=RemoteLinkStatus.UNLINKED,
                message="Lecture provider indisponible pour lier la playlist distante.",
            )
        if not matches:
            return RemotePlaylistLinkResult(
                status=RemoteLinkStatus.UNLINKED,
                message=f"Playlist distante introuvable : {name!r}.",
            )
        if len(matches) > 1:
            return RemotePlaylistLinkResult(
                status=RemoteLinkStatus.AMBIGUOUS,
                message=(
                    f"Plusieurs playlists distantes portent le nom {name!r} — "
                    "associez manuellement un identifiant distant."
                ),
            )
        return self._resolve_existing(read_port, matches[0].remote_playlist_id.strip())

    def _resolve_existing(
        self,
        read_port: ProviderPlaylistReadPort | None,
        remote_playlist_id: str,
    ) -> RemotePlaylistLinkResult:
        remote_id = remote_playlist_id.strip()
        if not remote_id:
            return RemotePlaylistLinkResult(
                status=RemoteLinkStatus.UNLINKED,
                message="Identifiant distant vide.",
            )
        if read_port is None:
            return RemotePlaylistLinkResult(
                status=RemoteLinkStatus.LINKED,
                remote_playlist_id=remote_id,
            )
        try:
            snapshot = read_port.get_playlist(remote_id)
        except (OSError, RuntimeError, ValueError) as exc:
            return RemotePlaylistLinkResult(
                status=RemoteLinkStatus.UNLINKED,
                message=f"Playlist distante introuvable pour l'identifiant {remote_id!r} : {exc}",
            )
        return RemotePlaylistLinkResult(
            status=RemoteLinkStatus.LINKED,
            remote_playlist_id=remote_id,
            snapshot_checksum=snapshot.checksum,
        )
