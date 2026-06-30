from __future__ import annotations

from playlist_builder.canonical.contracts import CatalogSearchPort
from playlist_builder.canonical.models import CanonicalSearchRequest, CanonicalTrack


def catalog_hint_for_track(
    track: CanonicalTrack,
    catalog: CatalogSearchPort,
    *,
    country_code: str = "us",
) -> str | None:
    """Return a catalog advisory when the local library search found nothing useful."""

    response = catalog.search(
        CanonicalSearchRequest(
            query=f"{track.artist.display_name} {track.title}".strip(),
            wanted_artist=track.artist.name,
            wanted_title=track.title,
            country_code=country_code,
        )
    )
    if not response.candidates:
        return None

    best = response.candidates[0]
    return (
        f"Catalogue iTunes: {best.track.label} "
        f"(confiance {best.raw_confidence:.0f}). "
        "Ajoutez ce morceau à votre bibliothèque Music pour l'importer."
    )


def enrich_resolution_message(
    track: CanonicalTrack,
    message: str,
    catalog: CatalogSearchPort | None,
    *,
    country_code: str = "us",
) -> str:
    if catalog is None:
        return message
    hint = catalog_hint_for_track(track, catalog, country_code=country_code)
    if hint is None:
        return message
    return f"{message} {hint}"
