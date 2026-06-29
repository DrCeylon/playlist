"""Provider-agnostic canonical domain model and integration contracts.

This package is the innermost layer of the architecture. It must not import
from application, integration, or infrastructure code.
"""

from playlist_builder.canonical.compat import (
    canonical_playlist_from_legacy,
    canonical_track_from_legacy,
    legacy_track_from_canonical,
    legacy_tracks_from_canonical_playlist,
)
from playlist_builder.canonical.constants import DEFAULT_PLAYLIST_DESCRIPTION
from playlist_builder.canonical.contracts import (
    CatalogSearchPort,
    LibraryResolvePort,
    PlaylistDeliveryPort,
    ProviderGateway,
)
from playlist_builder.canonical.enums import (
    ConfidenceLevel,
    ImportStatus,
    ProviderCapability,
    ProviderId,
    ResolutionDecision,
)
from playlist_builder.canonical.identity import track_identity_key
from playlist_builder.canonical.models import (
    CanonicalAlbum,
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalImportResult,
    CanonicalPlaylist,
    CanonicalPlaylistSection,
    CanonicalResolution,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.canonical.validation import (
    ValidationError,
    validate_playlist,
    validate_search_request,
    validate_track,
)

__all__ = [
    "DEFAULT_PLAYLIST_DESCRIPTION",
    "CanonicalAlbum",
    "CanonicalArtist",
    "CanonicalCandidate",
    "CanonicalImportResult",
    "CanonicalPlaylist",
    "CanonicalPlaylistSection",
    "CanonicalResolution",
    "CanonicalSearchRequest",
    "CanonicalSearchResponse",
    "CanonicalTrack",
    "CatalogSearchPort",
    "ConfidenceLevel",
    "ImportStatus",
    "LibraryResolvePort",
    "PlaylistDeliveryPort",
    "ProviderCapability",
    "ProviderGateway",
    "ProviderId",
    "ResolutionDecision",
    "ValidationError",
    "canonical_playlist_from_legacy",
    "canonical_track_from_legacy",
    "legacy_track_from_canonical",
    "legacy_tracks_from_canonical_playlist",
    "track_identity_key",
    "validate_playlist",
    "validate_search_request",
    "validate_track",
]
