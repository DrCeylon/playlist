from __future__ import annotations

import pytest

from playlist_builder.canonical import (
    DEFAULT_PLAYLIST_DESCRIPTION,
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalPlaylist,
    CanonicalPlaylistSection,
    CanonicalResolution,
    CanonicalSearchRequest,
    CanonicalTrack,
    ConfidenceLevel,
    ImportStatus,
    ProviderCapability,
    ProviderId,
    ResolutionDecision,
    ValidationError,
    canonical_playlist_from_legacy,
    canonical_track_from_legacy,
    legacy_track_from_canonical,
    legacy_tracks_from_canonical_playlist,
    track_identity_key,
    validate_playlist,
    validate_search_request,
    validate_track,
)
from playlist_builder.canonical.contracts import (
    CatalogSearchPort,
    LibraryResolvePort,
    PlaylistDeliveryPort,
    ProviderGateway,
)
from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.canonical.identity import normalize_identity_component
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackRef


def test_track_identity_key_normalizes_simple_values():
    assert track_identity_key("Kygo", "Firestone") == "kygo::firestone"


def test_track_identity_key_prefers_isrc_when_available():
    assert track_identity_key("Kygo", "Firestone", isrc="USRC123") == "isrc::usrc123"


def test_normalize_identity_component_strips_accents():
    assert normalize_identity_component("Gérudo") == "gerudo"


def test_canonical_track_label_and_validation():
    track = CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="Firestone")
    assert track.label == "Kygo - Firestone"
    validate_track(track)


def test_validate_track_rejects_empty_title():
    track = CanonicalTrack(artist=CanonicalArtist(name="Kygo"), title="  ")
    with pytest.raises(ValidationError):
        validate_track(track)


def test_validate_search_request_requires_positive_limit():
    with pytest.raises(ValidationError):
        validate_search_request(CanonicalSearchRequest(query="Kygo", limit=0))


def test_validate_playlist_requires_sections():
    with pytest.raises(ValidationError):
        validate_playlist(
            CanonicalPlaylist(name="Test", sections=())
        )


def test_legacy_track_round_trip_preserves_section():
    legacy = TrackRef(artist="Kygo", title="Firestone", section="Warm Up")
    canonical = canonical_track_from_legacy(legacy)
    restored = legacy_track_from_canonical(canonical, section=legacy.section)

    assert restored.artist == legacy.artist
    assert restored.title == legacy.title
    assert restored.section == legacy.section
    assert restored.key == legacy.key


def test_track_ref_to_canonical_shim():
    legacy = TrackRef(artist="Kygo", title="Firestone")
    canonical = legacy.to_canonical()

    assert canonical.identity_key == legacy.key
    assert TrackRef.from_canonical(canonical, section="Main").section == "Main"


def test_canonical_playlist_from_legacy_definition():
    legacy = PlaylistDefinition(
        name="Pool Party",
        sections=(
            PlaylistSection(
                name="Warm Up",
                tracks=(TrackRef("Kygo", "Firestone", section="Warm Up"),),
            ),
        ),
    )

    canonical = canonical_playlist_from_legacy(legacy)
    validate_playlist(canonical)
    assert canonical.name == "Pool Party"
    assert canonical.sections[0].name == "Warm Up"
    assert canonical.tracks[0].title == "Firestone"


def test_legacy_tracks_from_canonical_playlist_flattens_sections():
    canonical = CanonicalPlaylist(
        name="Test",
        sections=(
            CanonicalPlaylistSection(
                name="A",
                tracks=(CanonicalTrack(CanonicalArtist("A1"), "One"),),
            ),
            CanonicalPlaylistSection(
                name="B",
                tracks=(CanonicalTrack(CanonicalArtist("B1"), "Three"),),
            ),
        ),
    )

    rows = legacy_tracks_from_canonical_playlist(canonical)
    assert [row.section for row in rows] == ["A", "B"]
    assert rows[0].label == "A1 - One"


def test_confidence_level_from_score_thresholds():
    assert ConfidenceLevel.from_score(90) is ConfidenceLevel.HIGH
    assert ConfidenceLevel.from_score(60) is ConfidenceLevel.MEDIUM
    assert ConfidenceLevel.from_score(10) is ConfidenceLevel.LOW


def test_provider_enums_are_str_enums():
    assert ProviderId.SPOTIFY == "spotify"
    assert ProviderCapability.CATALOG_SEARCH == "catalog_search"
    assert ImportStatus.ADDED == "added"
    assert ResolutionDecision.AMBIGUOUS == "ambiguous"


def test_default_playlist_description_is_provider_neutral():
    assert "Apple Music" not in DEFAULT_PLAYLIST_DESCRIPTION


def test_canonical_resolution_and_candidate_models():
    requested = CanonicalTrack(CanonicalArtist("Kygo"), "Firestone")
    candidate = CanonicalCandidate(track=requested, source="itunes_search", raw_confidence=88.0)
    resolution = CanonicalResolution(
        requested=requested,
        selected=candidate,
        confidence=88.0,
        decision=ResolutionDecision.ACCEPTED,
    )

    assert resolution.selected is candidate


class _FakeCatalog(CatalogSearchPort):
    def search(self, request: CanonicalSearchRequest):
        return request  # type: ignore[return-value]


class _FakeLibrary(LibraryResolvePort):
    def collect_candidates(self, track: CanonicalTrack) -> tuple[CanonicalCandidate, ...]:
        return (CanonicalCandidate(track=track, source="fake"),)


class _FakeDelivery(PlaylistDeliveryPort):
    def import_playlist(self, playlist: CanonicalPlaylist):
        return playlist  # type: ignore[return-value]


class _FakeGateway(ProviderGateway):
    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.SPOTIFY

    @property
    def capabilities(self) -> frozenset[ProviderCapability]:
        return frozenset({ProviderCapability.CATALOG_SEARCH})

    @property
    def catalog(self) -> CatalogSearchPort:
        return _FakeCatalog()

    @property
    def library(self) -> LibraryResolvePort | None:
        return None

    @property
    def delivery(self) -> PlaylistDeliveryPort | None:
        return None

    @property
    def playlist_read(self) -> ProviderPlaylistReadPort | None:
        return None

    @property
    def playlist_write(self) -> ProviderPlaylistWritePort | None:
        return None


def test_provider_gateway_protocol_is_runtime_checkable():
    gateway = _FakeGateway()
    assert isinstance(gateway, ProviderGateway)
    assert isinstance(gateway.catalog, CatalogSearchPort)
    assert gateway.library is None

    library_gateway = _FakeLibrary()
    assert isinstance(library_gateway, LibraryResolvePort)

    delivery_gateway = _FakeDelivery()
    assert isinstance(delivery_gateway, PlaylistDeliveryPort)
