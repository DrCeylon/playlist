from __future__ import annotations

from unittest.mock import MagicMock

from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.integration.apple_music.catalog_fallback import (
    catalog_hint_for_track,
    enrich_resolution_message,
)


def _track() -> CanonicalTrack:
    return CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone")


def test_catalog_hint_returns_itunes_match_label():
    catalog = MagicMock()
    catalog.search.return_value = CanonicalSearchResponse(
        request=CanonicalSearchRequest(query="Kygo Firestone"),
        candidates=(
            CanonicalCandidate(
                track=_track(),
                source="apple_music_catalog",
                raw_confidence=92.0,
            ),
        ),
    )

    hint = catalog_hint_for_track(_track(), catalog)

    assert hint is not None
    assert "Kygo - Firestone" in hint
    assert "92" in hint
    assert "bibliothèque Music" in hint


def test_catalog_hint_returns_none_when_catalog_empty():
    catalog = MagicMock()
    catalog.search.return_value = CanonicalSearchResponse(
        request=CanonicalSearchRequest(query="Unknown"),
        candidates=(),
    )

    assert catalog_hint_for_track(_track(), catalog) is None


def test_enrich_resolution_message_appends_catalog_hint():
    catalog = MagicMock()
    catalog.search.return_value = CanonicalSearchResponse(
        request=CanonicalSearchRequest(query="Kygo Firestone"),
        candidates=(
            CanonicalCandidate(
                track=_track(),
                source="apple_music_catalog",
                raw_confidence=88.0,
            ),
        ),
    )

    message = enrich_resolution_message(
        _track(),
        "Aucun candidat retourné par Music.app.",
        catalog,
    )

    assert "Aucun candidat retourné" in message
    assert "Catalogue iTunes" in message
