from __future__ import annotations

from unittest.mock import MagicMock

from playlist_builder.canonical.models import (
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.integration.apple_music.library_acquisition import AppleMusicLibraryAcquisition
from playlist_builder.integration.apple_music.resolver import (
    AppleMusicResolutionStatus,
    AppleMusicResolver,
)
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.infrastructure.cache.identity_cache import IdentityCache


def _track() -> CanonicalTrack:
    return CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone")


def test_resolver_acquires_from_catalog_then_resolves(tmp_path):
    identity_cache = IdentityCache(JsonCache(tmp_path / "identity.json"))
    applescript = MagicMock()
    applescript.collect_candidates_batch.side_effect = [
        [[]],
        [
            [
                __import__(
                    "playlist_builder.integration.apple_music.models",
                    fromlist=["AppleMusicTrack"],
                ).AppleMusicTrack(
                    persistent_id="PID-NEW",
                    artist="Kygo",
                    title="Firestone (feat. Conrad Sewell)",
                    query="Firestone",
                )
            ]
        ],
    ]
    applescript.try_add_catalog_url.return_value = "PID-NEW"

    catalog = MagicMock()
    catalog.search.return_value = CanonicalSearchResponse(
        request=CanonicalSearchRequest(query="Kygo Firestone"),
        candidates=(
            CanonicalCandidate(
                track=_track(),
                source="apple_music_catalog",
                provider_hints=("https://music.apple.com/us/song/firestone/123",),
                raw_confidence=80.0,
            ),
        ),
    )

    resolver = AppleMusicResolver(
        applescript,
        identity_cache,
        catalog=catalog,
        acquire_missing=True,
        catalog_acquisition_min_confidence=70.0,
    )

    outcome = resolver.resolve(_track())

    assert outcome.status == AppleMusicResolutionStatus.RESOLVED
    assert outcome.persistent_id == "PID-NEW"
    assert outcome.catalog_acquired is True
    applescript.try_add_catalog_url.called
    applescript.acquire_song_from_url.assert_not_called()
