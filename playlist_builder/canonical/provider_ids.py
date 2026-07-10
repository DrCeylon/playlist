from __future__ import annotations

from playlist_builder.canonical.enums import ProviderId

PROVIDER_DISPLAY_NAMES: dict[ProviderId, str] = {
    ProviderId.APPLE_MUSIC: "Apple Music",
    ProviderId.APPLE_MUSICKIT: "Apple Music (MusicKit)",
    ProviderId.SPOTIFY: "Spotify",
    ProviderId.YOUTUBE_MUSIC: "YouTube Music",
    ProviderId.DEEZER: "Deezer",
    ProviderId.SOUNDCLOUD: "SoundCloud",
    ProviderId.TIDAL: "Tidal",
    ProviderId.QOBUZ: "Qobuz",
    ProviderId.BANDCAMP: "Bandcamp",
    ProviderId.PLEX: "Plex",
    ProviderId.JELLYFIN: "Jellyfin",
    ProviderId.NAVIDROME: "Navidrome",
    ProviderId.SUBSONIC: "Subsonic",
    ProviderId.LOCAL_FILES: "Local files",
    ProviderId.DISCOGS: "Discogs",
    ProviderId.MUSICBRAINZ: "MusicBrainz",
}


def provider_display_name(provider_id: ProviderId) -> str:
    return PROVIDER_DISPLAY_NAMES.get(provider_id, provider_id.value.replace("_", " ").title())


def parse_provider_id(raw: object, *, default: ProviderId | None = None) -> ProviderId:
    """Parse a provider id string. Unknown values raise — never silently coerce."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        if default is not None:
            return default
        raise ValueError("provider_id is required")
    try:
        return ProviderId(str(raw))
    except ValueError as exc:
        raise ValueError(f"Unknown provider_id: {raw!r}") from exc
