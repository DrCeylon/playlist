from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.canonical.enums import ProviderCapability, ProviderId


@dataclass(frozen=True, slots=True)
class ProviderOption:
    provider_id: ProviderId
    display_name: str
    is_available: bool
    is_connected: bool = False
    capabilities: frozenset[ProviderCapability] = frozenset()
    unavailable_reason: str = ""


def default_provider_options() -> tuple[ProviderOption, ...]:
    """Known providers for the UI selector (only Apple Music is active today)."""
    return (
        ProviderOption(
            provider_id=ProviderId.APPLE_MUSIC,
            display_name="Apple Music",
            is_available=True,
            is_connected=True,
            capabilities=frozenset(
                {
                    ProviderCapability.CATALOG_SEARCH,
                    ProviderCapability.LIBRARY_RESOLVE,
                    ProviderCapability.PLAYLIST_DELIVERY,
                }
            ),
        ),
        ProviderOption(
            provider_id=ProviderId.SPOTIFY,
            display_name="Spotify",
            is_available=False,
            unavailable_reason="Prévu — gateway non enregistré.",
        ),
        ProviderOption(
            provider_id=ProviderId.YOUTUBE_MUSIC,
            display_name="YouTube Music",
            is_available=False,
            unavailable_reason="Prévu — gateway non enregistré.",
        ),
        ProviderOption(
            provider_id=ProviderId.DEEZER,
            display_name="Deezer",
            is_available=False,
            unavailable_reason="Prévu — gateway non enregistré.",
        ),
    )
