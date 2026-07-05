from __future__ import annotations

from collections.abc import Callable

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalImportResult, CanonicalPlaylist, CanonicalTrack
from playlist_builder.integration.apple_music.import_service import AppleMusicImportService
from playlist_builder.integration.apple_music.resolver import (
    AppleMusicResolutionOutcome,
    AppleMusicResolutionStatus,
    AppleMusicResolver,
)
from playlist_builder.integration.ports.provider_import import (
    ManualAcquisitionHook,
    ProviderImportPort,
    ProviderImportResolutionOutcome,
    ProviderImportResolutionStatus,
    ProviderImportRuntimeLabels,
)

_APPLE_RUNTIME_LABELS = ProviderImportRuntimeLabels(
    provider_display_name="Apple Music",
    runtime_app_name="Music.app",
    connect_message="Connexion à Music.app via AppleScript…",
    runtime_ready_message="Music.app lancé en arrière-plan ({duration_ms} ms, sans activer la fenêtre)",
    delivery_start_message="Création/synchronisation de la playlist « {playlist_name} » dans Music.app…",
    delivery_batch_message="Ajout Music.app — lot {batch_index}/{batch_count}",
    delivery_complete_message="Synchronisation Music.app terminée en {duration_ms} ms",
    delivery_confirm_message="Confirmation Music.app : {added_count} morceau(x) visible(s) dans la playlist",
    not_found_message="Introuvable dans Apple Music",
)


class AppleMusicProviderImportPort:
    """Apple Music implementation of ProviderImportPort for bridge streaming import."""

    def __init__(self, import_service: AppleMusicImportService) -> None:
        self._import_service = import_service
        self._apple_outcomes: dict[str, AppleMusicResolutionOutcome] = {}

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.APPLE_MUSIC

    @property
    def runtime_labels(self) -> ProviderImportRuntimeLabels:
        return _APPLE_RUNTIME_LABELS

    @property
    def _resolver(self) -> AppleMusicResolver:
        return self._import_service.resolver

    def configure_manual_acquisition(self, hook: ManualAcquisitionHook | None) -> None:
        self._resolver._manual_acquisition_hook = hook  # noqa: SLF001

    def ensure_runtime_ready(self, *, activate: bool = False) -> None:
        self._import_service.applescript.ensure_running(activate=activate)

    def resolve_batch(
        self,
        rows: list[tuple[CanonicalTrack, str]],
    ) -> list[ProviderImportResolutionOutcome]:
        apple_outcomes = self._resolver.resolve_batch(rows)
        self._remember_apple_outcomes(apple_outcomes)
        return [_to_provider_outcome(item) for item in apple_outcomes]

    def resolve(self, track: CanonicalTrack, *, section: str = "Playlist") -> ProviderImportResolutionOutcome:
        apple_outcome = self._resolver.resolve(track, section=section)
        self._remember_apple_outcomes([apple_outcome])
        return _to_provider_outcome(apple_outcome)

    def probe_library_presence(self, track: CanonicalTrack, *, section: str = "Playlist") -> bool:
        return self._resolver.probe_library_presence(track, section=section)

    def ensure_playlist(self, name: str) -> None:
        self._import_service.delivery.ensure_playlist(name)

    def deliver_playlist(
        self,
        playlist: CanonicalPlaylist,
        outcomes: list[ProviderImportResolutionOutcome],
        *,
        on_delivery_batch: Callable[[int, int], None] | None = None,
    ) -> CanonicalImportReport:
        apple_outcomes = [self._require_apple_outcome(item) for item in outcomes]
        return self._import_service.delivery.sync_playlist(
            playlist,
            apple_outcomes,
            on_delivery_batch=on_delivery_batch,
        )

    def add_resolved_track(
        self,
        playlist_name: str,
        outcome: ProviderImportResolutionOutcome,
        *,
        section_name: str,
        existing_keys: set[str] | None = None,
    ) -> CanonicalImportResult:
        apple_outcome = self._require_apple_outcome(outcome)
        return self._import_service.delivery.add_resolved_track(
            playlist_name,
            apple_outcome,
            section_name=section_name,
            existing_keys=existing_keys,
        )

    def _remember_apple_outcomes(self, outcomes: list[AppleMusicResolutionOutcome]) -> None:
        for outcome in outcomes:
            self._apple_outcomes[outcome.track.identity_key] = outcome

    def _require_apple_outcome(
        self,
        outcome: ProviderImportResolutionOutcome,
    ) -> AppleMusicResolutionOutcome:
        apple_outcome = self._apple_outcomes.get(outcome.track.identity_key)
        if apple_outcome is None:
            raise ValueError(
                f"Aucun résultat provider interne pour {outcome.track.label!r}. "
                "Appelez resolve/resolve_batch avant delivery."
            )
        return apple_outcome


def _to_provider_outcome(outcome: AppleMusicResolutionOutcome) -> ProviderImportResolutionOutcome:
    return ProviderImportResolutionOutcome(
        track=outcome.track,
        status=_map_status(outcome.status),
        cache_hit=outcome.cache_hit,
        catalog_acquired=outcome.catalog_acquired,
        error=outcome.error,
    )


def _map_status(status: AppleMusicResolutionStatus) -> ProviderImportResolutionStatus:
    return {
        AppleMusicResolutionStatus.RESOLVED: ProviderImportResolutionStatus.RESOLVED,
        AppleMusicResolutionStatus.NOT_FOUND: ProviderImportResolutionStatus.NOT_FOUND,
        AppleMusicResolutionStatus.ERROR: ProviderImportResolutionStatus.ERROR,
    }[status]
