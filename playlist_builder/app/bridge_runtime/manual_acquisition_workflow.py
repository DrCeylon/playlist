from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from playlist_builder.canonical.compat import canonical_playlist_from_legacy, legacy_track_from_canonical
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.resolver.query import generate_query_variants
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode

if TYPE_CHECKING:
    from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
    from playlist_builder.app.factory import AppContext


class ManualAcquisitionWorkflowPhase(StrEnum):
    """Explicit workflow phases for manual acquisition resume (ADR-012 step 5)."""

    WAITING_FOR_USER = "waiting_for_user"
    VERIFYING_LIBRARY = "verifying_library"
    TRACK_FOUND = "track_found"
    UPDATING_IDENTITY_CACHE = "updating_identity_cache"
    RESUMING_IMPORT = "resuming_import"
    DELIVERING_PLAYLIST = "delivering_playlist"
    COMPLETED = "completed"
    FAILED = "failed"
    CHECKPOINT_EXPIRED = "checkpoint_expired"


_ALLOWED_TRANSITIONS: dict[ManualAcquisitionWorkflowPhase, frozenset[ManualAcquisitionWorkflowPhase]] = {
    ManualAcquisitionWorkflowPhase.WAITING_FOR_USER: frozenset(
        {
            ManualAcquisitionWorkflowPhase.VERIFYING_LIBRARY,
            ManualAcquisitionWorkflowPhase.RESUMING_IMPORT,
            ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED,
            ManualAcquisitionWorkflowPhase.FAILED,
        }
    ),
    ManualAcquisitionWorkflowPhase.VERIFYING_LIBRARY: frozenset(
        {
            ManualAcquisitionWorkflowPhase.TRACK_FOUND,
            ManualAcquisitionWorkflowPhase.WAITING_FOR_USER,
            ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED,
            ManualAcquisitionWorkflowPhase.FAILED,
            ManualAcquisitionWorkflowPhase.UPDATING_IDENTITY_CACHE,
        }
    ),
    ManualAcquisitionWorkflowPhase.TRACK_FOUND: frozenset(
        {
            ManualAcquisitionWorkflowPhase.UPDATING_IDENTITY_CACHE,
            ManualAcquisitionWorkflowPhase.RESUMING_IMPORT,
            ManualAcquisitionWorkflowPhase.FAILED,
        }
    ),
    ManualAcquisitionWorkflowPhase.UPDATING_IDENTITY_CACHE: frozenset(
        {
            ManualAcquisitionWorkflowPhase.TRACK_FOUND,
            ManualAcquisitionWorkflowPhase.RESUMING_IMPORT,
            ManualAcquisitionWorkflowPhase.WAITING_FOR_USER,
            ManualAcquisitionWorkflowPhase.FAILED,
        }
    ),
    ManualAcquisitionWorkflowPhase.RESUMING_IMPORT: frozenset(
        {
            ManualAcquisitionWorkflowPhase.DELIVERING_PLAYLIST,
            ManualAcquisitionWorkflowPhase.WAITING_FOR_USER,
            ManualAcquisitionWorkflowPhase.COMPLETED,
            ManualAcquisitionWorkflowPhase.FAILED,
            ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED,
        }
    ),
    ManualAcquisitionWorkflowPhase.DELIVERING_PLAYLIST: frozenset(
        {
            ManualAcquisitionWorkflowPhase.COMPLETED,
            ManualAcquisitionWorkflowPhase.FAILED,
            ManualAcquisitionWorkflowPhase.WAITING_FOR_USER,
        }
    ),
    ManualAcquisitionWorkflowPhase.COMPLETED: frozenset(),
    ManualAcquisitionWorkflowPhase.FAILED: frozenset({ManualAcquisitionWorkflowPhase.WAITING_FOR_USER}),
    ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED: frozenset({ManualAcquisitionWorkflowPhase.WAITING_FOR_USER}),
}


def can_transition(
    current: ManualAcquisitionWorkflowPhase,
    target: ManualAcquisitionWorkflowPhase,
) -> bool:
    if current == target:
        return True
    return target in _ALLOWED_TRANSITIONS.get(current, frozenset())


@dataclass(slots=True)
class ManualAcquisitionWorkflowCoordinator:
    """Single orchestrator for manual acquisition probe/resume on the bridge backend."""

    context: AppContext
    session_store: ImportSessionStore
    _phase: ManualAcquisitionWorkflowPhase = ManualAcquisitionWorkflowPhase.WAITING_FOR_USER

    @property
    def phase(self) -> ManualAcquisitionWorkflowPhase:
        return self._phase

    def reset(self) -> None:
        self._phase = ManualAcquisitionWorkflowPhase.WAITING_FOR_USER

    def transition(self, target: ManualAcquisitionWorkflowPhase) -> None:
        if not can_transition(self._phase, target):
            raise ValueError(
                f"Transition manuelle interdite : {self._phase.value} → {target.value}"
            )
        self._phase = target

    def probe_manual_acquisition(self, params: dict) -> dict[str, object]:
        session_id = str(params.get("import_session_id", "")).strip()
        if not session_id:
            raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "import_session_id est requis.")

        initiator = str(params.get("initiator", "user")).strip().lower()
        if self._phase == ManualAcquisitionWorkflowPhase.WAITING_FOR_USER:
            self.transition(ManualAcquisitionWorkflowPhase.VERIFYING_LIBRARY)
        elif self._phase != ManualAcquisitionWorkflowPhase.VERIFYING_LIBRARY:
            self.transition(ManualAcquisitionWorkflowPhase.VERIFYING_LIBRARY)

        checkpoint_path = str(self.session_store.path_for(session_id).resolve())
        checkpoint_exists = self.session_store.exists(session_id)
        if not checkpoint_exists:
            self.transition(ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED)
            return self._probe_payload(
                found=False,
                message="La session d'import a expiré. Relancez l'import depuis l'aperçu.",
                error_code="checkpoint_missing",
                workflow_phase=ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED,
                diagnostics={
                    "import_session_id": session_id,
                    "checkpoint_path": checkpoint_path,
                    "checkpoint_exists": False,
                    "search_terms": [],
                    "provider_id": ProviderId.APPLE_MUSIC.value,
                    "probe_error": None,
                    "initiator": initiator,
                },
            )

        if sys.platform != "darwin":
            self.transition(ManualAcquisitionWorkflowPhase.FAILED)
            return self._probe_payload(
                found=False,
                message="Disponible uniquement sur macOS.",
                error_code="platform_unavailable",
                workflow_phase=ManualAcquisitionWorkflowPhase.FAILED,
                diagnostics={
                    "import_session_id": session_id,
                    "checkpoint_path": checkpoint_path,
                    "checkpoint_exists": True,
                    "search_terms": [],
                    "provider_id": ProviderId.APPLE_MUSIC.value,
                    "probe_error": None,
                    "initiator": initiator,
                },
            )

        from playlist_builder.app.factory import get_provider_import_port

        import_port = get_provider_import_port(self.context)
        labels = import_port.runtime_labels
        checkpoint = self.session_store.load(session_id)
        if checkpoint is None:
            self.transition(ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED)
            return self._probe_payload(
                found=False,
                message="La session d'import a expiré. Relancez l'import depuis l'aperçu.",
                error_code="checkpoint_missing",
                workflow_phase=ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED,
                diagnostics={
                    "import_session_id": session_id,
                    "checkpoint_path": checkpoint_path,
                    "checkpoint_exists": False,
                    "search_terms": [],
                    "provider_id": import_port.provider_id.value,
                    "probe_error": None,
                    "initiator": initiator,
                },
            )

        canonical = canonical_playlist_from_legacy(checkpoint.playlist)
        rows = [(track, section.name) for section in canonical.sections for track in section.tracks]
        if checkpoint.next_index >= len(rows):
            self.transition(ManualAcquisitionWorkflowPhase.FAILED)
            return self._probe_payload(
                found=False,
                message="Aucun morceau en attente.",
                error_code="no_pending_track",
                workflow_phase=ManualAcquisitionWorkflowPhase.FAILED,
                diagnostics={
                    "import_session_id": session_id,
                    "checkpoint_path": checkpoint_path,
                    "checkpoint_exists": True,
                    "search_terms": [],
                    "provider_id": import_port.provider_id.value,
                    "probe_error": None,
                    "initiator": initiator,
                },
            )

        track, section_name = rows[checkpoint.next_index]
        legacy = legacy_track_from_canonical(track, section=section_name)
        search_terms = [variant.term for variant in generate_query_variants(legacy)]
        probe_started_at = time.time()

        self.transition(ManualAcquisitionWorkflowPhase.UPDATING_IDENTITY_CACHE)
        probe_detail = getattr(import_port, "probe_library_presence_detail", None)
        if callable(probe_detail):
            found, probe_error = probe_detail(track, section=section_name)
        else:
            found = import_port.probe_library_presence(track, section=section_name)
            probe_error = None

        probe_finished_at = time.time()
        probe_duration_ms = int((probe_finished_at - probe_started_at) * 1000)

        diagnostics: dict[str, object] = {
            "import_session_id": session_id,
            "checkpoint_path": checkpoint_path,
            "checkpoint_exists": True,
            "search_terms": search_terms,
            "provider_id": import_port.provider_id.value,
            "probe_error": probe_error,
            "probe_started_at": probe_started_at,
            "probe_finished_at": probe_finished_at,
            "probe_duration_ms": probe_duration_ms,
            "initiator": initiator,
        }

        if probe_error:
            self.transition(ManualAcquisitionWorkflowPhase.FAILED)
            return self._probe_payload(
                found=False,
                message=f"Erreur technique lors de la vérification bibliothèque : {probe_error}",
                error_code="probe_error",
                workflow_phase=ManualAcquisitionWorkflowPhase.FAILED,
                diagnostics=diagnostics,
            )

        if found:
            self.transition(ManualAcquisitionWorkflowPhase.TRACK_FOUND)
            return self._probe_payload(
                found=True,
                message=f"Morceau détecté dans la bibliothèque {labels.runtime_app_name}.",
                error_code=None,
                workflow_phase=ManualAcquisitionWorkflowPhase.TRACK_FOUND,
                diagnostics=diagnostics,
            )

        self.transition(ManualAcquisitionWorkflowPhase.WAITING_FOR_USER)
        return self._probe_payload(
            found=False,
            message=(
                "Morceau pas encore détecté dans la bibliothèque. "
                "Vérifiez qu'il a bien été ajouté dans Music.app, puis réessayez."
            ),
            error_code="track_not_found",
            workflow_phase=ManualAcquisitionWorkflowPhase.WAITING_FOR_USER,
            diagnostics=diagnostics,
        )

    def mark_resuming_import(self) -> None:
        self.transition(ManualAcquisitionWorkflowPhase.RESUMING_IMPORT)

    @staticmethod
    def _probe_payload(
        *,
        found: bool,
        message: str,
        error_code: str | None,
        workflow_phase: ManualAcquisitionWorkflowPhase,
        diagnostics: dict[str, object],
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "found": found,
            "message": message,
            "workflow_phase": workflow_phase.value,
            "diagnostics": diagnostics,
        }
        if error_code is not None:
            payload["error_code"] = error_code
        return payload
