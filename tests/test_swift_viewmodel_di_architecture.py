from __future__ import annotations

from pathlib import Path


RESONANCE_MAC = Path("apps/resonance/ResonanceMac/Sources/ResonanceMac")
COORDINATOR = RESONANCE_MAC / "Support" / "AppWorkflowCoordinator.swift"

FORBIDDEN_SWIFT_PATTERNS = (
    "replaceService(",
    "replaceServices(",
)

COORDINATOR_OWNED_VIEW_MODELS = (
    "syncViewModel",
    "providersViewModel",
    "historyViewModel",
    "diagnosticsViewModel",
    "playlistBuilder",
    "importWorkflow",
    "libraryStore",
)

SCREEN_VIEW_FILES = (
    RESONANCE_MAC / "Screens" / "SyncView.swift",
    RESONANCE_MAC / "Screens" / "ProvidersView.swift",
    RESONANCE_MAC / "Screens" / "HistoryView.swift",
    RESONANCE_MAC / "Screens" / "DiagnosticsView.swift",
)


def test_swift_viewmodels_have_no_late_service_swap() -> None:
    offenders: list[str] = []
    for path in RESONANCE_MAC.rglob("*.swift"):
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_SWIFT_PATTERNS:
            if pattern in text:
                offenders.append(f"{path}: contains {pattern!r}")
    assert offenders == []


def test_app_workflow_coordinator_owns_screen_view_models() -> None:
    text = COORDINATOR.read_text(encoding="utf-8")
    for symbol in COORDINATOR_OWNED_VIEW_MODELS:
        assert f"let {symbol}:" in text, f"missing coordinator-owned view model {symbol}"


def test_screen_views_receive_coordinator_view_models() -> None:
    for path in SCREEN_VIEW_FILES:
        text = path.read_text(encoding="utf-8")
        assert "@StateObject" not in text, f"{path} still constructs its own @StateObject view model"
        assert "workflow." in text or "@ObservedObject" in text, f"{path} should observe coordinator view models"


def test_production_view_models_use_immutable_dependencies() -> None:
    view_models = (
        RESONANCE_MAC / "ViewModels" / "SyncViewModel.swift",
        RESONANCE_MAC / "ViewModels" / "ProvidersViewModel.swift",
        RESONANCE_MAC / "ViewModels" / "HistoryViewModel.swift",
        RESONANCE_MAC / "ViewModels" / "DiagnosticsViewModel.swift",
        RESONANCE_MAC / "ViewModels" / "PlaylistLibraryStore.swift",
    )
    for path in view_models:
        text = path.read_text(encoding="utf-8")
        assert "private let" in text, f"{path} should keep immutable injected dependencies"
        assert "private var service" not in text, f"{path} should not use mutable service storage"
