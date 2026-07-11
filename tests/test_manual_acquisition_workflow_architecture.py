from __future__ import annotations

import inspect
import sys
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.app.bridge_runtime.backend import RuntimeEngineBridgeBackend
from playlist_builder.app.bridge_runtime.import_session import ImportSessionStore
from playlist_builder.app.bridge_runtime.manual_acquisition_workflow import (
    ManualAcquisitionWorkflowCoordinator,
    ManualAcquisitionWorkflowPhase,
    can_transition,
)
from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings


def test_manual_workflow_phase_transition_matrix_is_explicit() -> None:
    assert can_transition(
        ManualAcquisitionWorkflowPhase.WAITING_FOR_USER,
        ManualAcquisitionWorkflowPhase.VERIFYING_LIBRARY,
    )
    assert can_transition(
        ManualAcquisitionWorkflowPhase.VERIFYING_LIBRARY,
        ManualAcquisitionWorkflowPhase.UPDATING_IDENTITY_CACHE,
    )
    assert can_transition(
        ManualAcquisitionWorkflowPhase.TRACK_FOUND,
        ManualAcquisitionWorkflowPhase.RESUMING_IMPORT,
    )
    assert not can_transition(
        ManualAcquisitionWorkflowPhase.COMPLETED,
        ManualAcquisitionWorkflowPhase.VERIFYING_LIBRARY,
    )
    assert not can_transition(
        ManualAcquisitionWorkflowPhase.WAITING_FOR_USER,
        ManualAcquisitionWorkflowPhase.COMPLETED,
    )


def test_manual_workflow_coordinator_reset_bypasses_transition_matrix() -> None:
    coordinator = ManualAcquisitionWorkflowCoordinator(
        context=MagicMock(),
        session_store=MagicMock(),
    )
    coordinator._phase = ManualAcquisitionWorkflowPhase.COMPLETED
    coordinator.reset()
    assert coordinator.phase == ManualAcquisitionWorkflowPhase.WAITING_FOR_USER
    assert not can_transition(
        ManualAcquisitionWorkflowPhase.COMPLETED,
        ManualAcquisitionWorkflowPhase.WAITING_FOR_USER,
    )


def test_manual_workflow_coordinator_rejects_illegal_transition(tmp_path) -> None:
    context = build_app_context(AppSettings(wait_for_manual_catalog_add=True))
    coordinator = ManualAcquisitionWorkflowCoordinator(
        context=context,
        session_store=ImportSessionStore(tmp_path / "checkpoints"),
    )
    coordinator.transition(ManualAcquisitionWorkflowPhase.VERIFYING_LIBRARY)
    coordinator.transition(ManualAcquisitionWorkflowPhase.TRACK_FOUND)
    with pytest.raises(ValueError, match="interdite"):
        coordinator.transition(ManualAcquisitionWorkflowPhase.COMPLETED)


def test_backend_probe_delegates_to_workflow_coordinator(tmp_path) -> None:
    store = ImportSessionStore(tmp_path / "checkpoints")
    backend = RuntimeEngineBridgeBackend(
        build_app_context(AppSettings(wait_for_manual_catalog_add=True)),
        session_store=store,
    )
    with patch.object(sys, "platform", "darwin"):
        result = backend.probe_manual_acquisition({"import_session_id": "missing-session"})

    assert result["found"] is False
    assert result["error_code"] == "checkpoint_missing"
    assert result["workflow_phase"] == ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED.value
    assert backend._manual_workflow.phase == ManualAcquisitionWorkflowPhase.CHECKPOINT_EXPIRED


def test_backend_is_thin_facade_for_manual_probe() -> None:
    source = inspect.getsource(RuntimeEngineBridgeBackend.probe_manual_acquisition)
    assert "_manual_workflow.probe_manual_acquisition" in source
    assert "probe_library_presence" not in source


def test_manual_workflow_coordinator_is_single_orchestrator_module() -> None:
    coordinator_source = inspect.getsource(ManualAcquisitionWorkflowCoordinator.probe_manual_acquisition)
    assert "workflow_phase" in coordinator_source
    assert "mark_resuming_import" in inspect.getsource(ManualAcquisitionWorkflowCoordinator)
