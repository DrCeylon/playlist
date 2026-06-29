"""Apple Music integration adapters."""

from playlist_builder.integration.apple_music.gateway import (
    AppleMusicProviderGateway,
    build_apple_music_gateway,
    build_apple_music_import_service,
    build_default_registry,
)

__all__ = [
    "AppleMusicProviderGateway",
    "build_apple_music_gateway",
    "build_apple_music_import_service",
    "build_default_registry",
]
