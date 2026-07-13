from __future__ import annotations

from collections.abc import Callable

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalImportResult, CanonicalPlaylist, CanonicalTrack
from playlist_builder.integration.ports.provider_import import (
    ManualAcquisitionHook,
    ProviderImportResolutionOutcome,
    ProviderImportResolutionStatus,
    ProviderImportRuntimeLabels,
)
from playlist_builder.integration.youtube_music.import_service import YouTubeMusicImportService
from playlist_builder.integration.youtube_music.resolver import YouTubeMusicResolutionOutcome, YouTubeMusicResolutionStatus

_YOUTUBE_RUNTIME_LABELS = ProviderImportRuntimeLabels(
    provider_display_name="YouTube Music",
    runtime_app_name="YouTube Music",
    connect_message="Connexion à YouTube Music…",
    runtime_ready_message="Compte YouTube Music connecté ({duration_ms} ms)",
    delivery_start_message="Création/synchronisation de la playlist « {playlist_name} » sur YouTube Music…",
    delivery_batch_message="Ajout YouTube Music — lot {batch_index}/{batch_count}",
    delivery_complete_message="Synchronisation YouTube Music terminée en {duration_ms} ms",
    delivery_confirm_message="Confirmation YouTube Music : {added_count} morceau(x) ajouté(s)",
    not_found_message="Introuvable sur YouTube Music",
)


class YouTubeMusicProviderImportPort:
    """YouTube Music implementation of ProviderImportPort for bridge streaming import."""

    def __init__(self, import_service: YouTubeMusicImportService) -> None:
        self._import_service = import_service
        self._youtube_outcomes: dict[str, YouTubeMusicResolutionOutcome] = {}

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId.YOUTUBE_MUSIC

    @property
    def runtime_labels(self) -> ProviderImportRuntimeLabels:
        return _YOUTUBE_RUNTIME_LABELS

    @property
    def _resolver(self):
        return self._import_service.resolver

    def configure_manual_acquisition(self, hook: ManualAcquisitionHook | None) -> None:
        del hook

    def ensure_runtime_ready(self, *, activate: bool = False) -> None:
        del activate
        if self._import_service._auth.headers_path() is None:  # noqa: SLF001
            raise ValueError("Connexion YouTube Music requise. Configurez vos en-têtes dans Services musicaux.")

    def resolve_batch(
        self,
        rows: list[tuple[CanonicalTrack, str]],
    ) -> list[ProviderImportResolutionOutcome]:
        youtube_outcomes = self._resolver.resolve_batch(rows)
        self._remember_youtube_outcomes(youtube_outcomes)
        return [_to_provider_outcome(item) for item in youtube_outcomes]

    def resolve(self, track: CanonicalTrack, *, section: str = "Playlist") -> ProviderImportResolutionOutcome:
        youtube_outcome = self._resolver.resolve(track, section=section)
        self._remember_youtube_outcomes([youtube_outcome])
        return _to_provider_outcome(youtube_outcome)

    def probe_library_presence(self, track: CanonicalTrack, *, section: str = "Playlist") -> bool:
        return self._resolver.probe_library_presence(track, section=section)

    def probe_library_presence_detail(
        self,
        track: CanonicalTrack,
        *,
        section: str = "Playlist",
    ) -> tuple[bool, str | None]:
        return self._resolver.probe_library_presence_detail(track, section=section)

    def ensure_playlist(self, name: str) -> None:
        self._import_service.delivery.ensure_playlist(name)

    def deliver_playlist(
        self,
        playlist: CanonicalPlaylist,
        outcomes: list[ProviderImportResolutionOutcome],
        *,
        on_delivery_batch: Callable[[int, int], None] | None = None,
    ) -> CanonicalImportReport:
        youtube_outcomes = [self._require_youtube_outcome(item) for item in outcomes]
        return self._import_service.delivery.sync_playlist(
            playlist,
            youtube_outcomes,
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
        youtube_outcome = self._require_youtube_outcome(outcome)
        return self._import_service.delivery.add_resolved_track(
            playlist_name,
            youtube_outcome,
            section_name=section_name,
            existing_keys=existing_keys,
        )

    def _remember_youtube_outcomes(self, outcomes: list[YouTubeMusicResolutionOutcome]) -> None:
        for outcome in outcomes:
            self._youtube_outcomes[outcome.track.identity_key] = outcome

    def _require_youtube_outcome(
        self,
        outcome: ProviderImportResolutionOutcome,
    ) -> YouTubeMusicResolutionOutcome:
        youtube_outcome = self._youtube_outcomes.get(outcome.track.identity_key)
        if youtube_outcome is None:
            raise ValueError(
                f"Aucun résultat provider interne pour {outcome.track.label!r}. "
                "Appelez resolve/resolve_batch avant delivery."
            )
        return youtube_outcome


def _to_provider_outcome(outcome: YouTubeMusicResolutionOutcome) -> ProviderImportResolutionOutcome:
    return ProviderImportResolutionOutcome(
        track=outcome.track,
        status=_map_status(outcome.status),
        error=outcome.error,
    )


def _map_status(status: YouTubeMusicResolutionStatus) -> ProviderImportResolutionStatus:
    return {
        YouTubeMusicResolutionStatus.RESOLVED: ProviderImportResolutionStatus.RESOLVED,
        YouTubeMusicResolutionStatus.NOT_FOUND: ProviderImportResolutionStatus.NOT_FOUND,
        YouTubeMusicResolutionStatus.ERROR: ProviderImportResolutionStatus.ERROR,
    }[status]
