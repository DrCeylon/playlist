from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.ui.shared.validation import dto_to_dict


class ProviderAuthState(StrEnum):
    """Bridge-safe provider authentication state — no secrets."""

    DISCONNECTED = "disconnected"
    CONFIGURED = "configured"
    CONNECTED = "connected"
    EXPIRED = "expired"
    ERROR = "error"
    EXPERIMENTAL_UNAVAILABLE = "experimental_unavailable"


@dataclass(frozen=True, slots=True)
class RemotePlaylistTrack:
    remote_track_id: str
    artist: str
    title: str
    album: str = ""
    duration_ms: int = 0
    position: int = 0
    provider_metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = dto_to_dict(self)
        if not self.provider_metadata:
            payload["provider_metadata"] = {}
        return payload


@dataclass(frozen=True, slots=True)
class RemotePlaylist:
    provider_id: ProviderId
    remote_playlist_id: str
    name: str
    track_count: int
    is_public: bool = False
    owner_label: str = ""
    snapshot_at_iso: str = ""
    source_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = dto_to_dict(self)
        payload["provider_id"] = self.provider_id.value
        return payload


@dataclass(frozen=True, slots=True)
class RemotePlaylistSnapshot:
    provider_id: ProviderId
    remote_playlist_id: str
    name: str
    snapshot_at_iso: str
    tracks: tuple[RemotePlaylistTrack, ...]
    track_count: int
    checksum: str
    source_kind: str
    source_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = dto_to_dict(self)
        payload["provider_id"] = self.provider_id.value
        payload["tracks"] = [track.to_dict() for track in self.tracks]
        return payload


@dataclass(frozen=True, slots=True)
class RemoteProviderAccount:
    provider_id: ProviderId
    display_name: str
    auth_state: ProviderAuthState
    last_connected_at_iso: str = ""
    capabilities: frozenset[ProviderCapability] = frozenset()

    def to_dict(self) -> dict[str, Any]:
        payload = dto_to_dict(self)
        payload["provider_id"] = self.provider_id.value
        payload["auth_state"] = self.auth_state.value
        payload["capabilities"] = sorted(capability.value for capability in self.capabilities)
        return payload


def remote_playlist_snapshot_checksum(tracks: tuple[RemotePlaylistTrack, ...]) -> str:
    """Stable hash of track keys and order for snapshot comparison."""
    parts: list[str] = []
    for track in tracks:
        parts.append(f"{track.position}:{track.remote_track_id}:{track.artist.strip().lower()}:{track.title.strip().lower()}")
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]
