from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.canonical.provider_ids import provider_display_name


@dataclass(frozen=True, slots=True)
class ProviderOption:
    provider_id: ProviderId
    display_name: str
    is_available: bool
    is_connected: bool = False
    capabilities: frozenset[ProviderCapability] = frozenset()
    unavailable_reason: str = ""
    is_experimental: bool = False


def default_provider_options() -> tuple[ProviderOption, ...]:
    """Display catalog for the provider picker. Registered gateways override availability at runtime."""
    planned = (
        ProviderId.APPLE_MUSIC,
        ProviderId.SPOTIFY,
        ProviderId.YOUTUBE_MUSIC,
        ProviderId.DEEZER,
        ProviderId.TIDAL,
        ProviderId.QOBUZ,
        ProviderId.SOUNDCLOUD,
        ProviderId.BANDCAMP,
        ProviderId.PLEX,
        ProviderId.JELLYFIN,
        ProviderId.NAVIDROME,
        ProviderId.SUBSONIC,
        ProviderId.LOCAL_FILES,
    )
    return tuple(
        ProviderOption(
            provider_id=provider_id,
            display_name=provider_display_name(provider_id),
            is_available=False,
            unavailable_reason="Gateway non enregistré.",
        )
        for provider_id in planned
    )
