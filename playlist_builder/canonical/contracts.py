from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.canonical.models import (
    CanonicalCandidate,
    CanonicalImportReport,
    CanonicalPlaylist,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)

if TYPE_CHECKING:
    from playlist_builder.integration.ports.playlist_read import ProviderPlaylistReadPort
    from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort


@runtime_checkable
class CatalogSearchPort(Protocol):
  """Search an external catalog for candidate tracks."""

  def search(self, request: CanonicalSearchRequest) -> CanonicalSearchResponse: ...


@runtime_checkable
class LibraryResolvePort(Protocol):
  """Collect resolution candidates from a user's connected library."""

  def collect_candidates(self, track: CanonicalTrack) -> tuple[CanonicalCandidate, ...]: ...


@runtime_checkable
class PlaylistDeliveryPort(Protocol):
  """Materialize a canonical playlist on a target platform."""

  def import_playlist(self, playlist: CanonicalPlaylist) -> CanonicalImportReport: ...


@runtime_checkable
class ProviderGateway(Protocol):
  """Provider-specific integration façade registered in the generic gateway."""

  @property
  def provider_id(self) -> ProviderId: ...

  @property
  def capabilities(self) -> frozenset[ProviderCapability]: ...

  @property
  def catalog(self) -> CatalogSearchPort | None: ...

  @property
  def library(self) -> LibraryResolvePort | None: ...

  @property
  def delivery(self) -> PlaylistDeliveryPort | None: ...

  @property
  def playlist_read(self) -> ProviderPlaylistReadPort | None: ...

  @property
  def playlist_write(self) -> ProviderPlaylistWritePort | None: ...
