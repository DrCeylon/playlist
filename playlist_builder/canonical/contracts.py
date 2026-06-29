from __future__ import annotations

from typing import Protocol, runtime_checkable

from playlist_builder.canonical.enums import ProviderCapability, ProviderId
from playlist_builder.canonical.models import (
    CanonicalCandidate,
    CanonicalImportReport,
    CanonicalPlaylist,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)


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
