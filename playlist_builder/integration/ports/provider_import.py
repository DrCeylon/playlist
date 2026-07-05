from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalImportResult, CanonicalPlaylist, CanonicalTrack

ManualAcquisitionHook = Callable[..., None]


class ProviderImportResolutionStatus(StrEnum):
    """Provider-neutral resolution status for bridge streaming import."""

    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ProviderImportResolutionOutcome:
    """Bridge-safe resolution outcome — no provider-specific identifiers."""

    track: CanonicalTrack
    status: ProviderImportResolutionStatus
    cache_hit: bool = False
    catalog_acquired: bool = False
    error: str = ""


@dataclass(frozen=True, slots=True)
class ProviderImportRuntimeLabels:
    """User-facing labels for provider runtime diagnostics (bridge only)."""

    provider_display_name: str
    runtime_app_name: str
    connect_message: str
    runtime_ready_message: str
    delivery_start_message: str
    delivery_batch_message: str
    delivery_complete_message: str
    delivery_confirm_message: str
    not_found_message: str


@runtime_checkable
class ProviderImportPort(Protocol):
    """Streaming playlist import port — hides provider resolver/delivery details."""

    @property
    def provider_id(self) -> ProviderId: ...

    @property
    def runtime_labels(self) -> ProviderImportRuntimeLabels: ...

    def configure_manual_acquisition(self, hook: ManualAcquisitionHook | None) -> None: ...

    def ensure_runtime_ready(self, *, activate: bool = False) -> None: ...

    def resolve_batch(
        self,
        rows: list[tuple[CanonicalTrack, str]],
    ) -> list[ProviderImportResolutionOutcome]: ...

    def resolve(self, track: CanonicalTrack, *, section: str = "Playlist") -> ProviderImportResolutionOutcome: ...

    def probe_library_presence(self, track: CanonicalTrack, *, section: str = "Playlist") -> bool: ...

    def ensure_playlist(self, name: str) -> None: ...

    def deliver_playlist(
        self,
        playlist: CanonicalPlaylist,
        outcomes: list[ProviderImportResolutionOutcome],
        *,
        on_delivery_batch: Callable[[int, int], None] | None = None,
    ) -> CanonicalImportReport: ...

    def add_resolved_track(
        self,
        playlist_name: str,
        outcome: ProviderImportResolutionOutcome,
        *,
        section_name: str,
        existing_keys: set[str] | None = None,
    ) -> CanonicalImportResult: ...
