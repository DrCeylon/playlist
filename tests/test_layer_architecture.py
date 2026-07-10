from __future__ import annotations

import ast
from pathlib import Path


def _collect_import_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
    return modules


def test_integration_ports_do_not_import_ui_layer() -> None:
    """Ports are inward contracts — they must not depend on presentation DTOs long-term.

    Today ports still reference ui.shared.dto (known debt). This guard prevents
    *new* UI imports from integration/ports beyond the existing remote_playlist surface.
    """
    root = Path("playlist_builder/integration/ports")
    allowed_ui_prefixes = (
        "playlist_builder.ui.shared.dto.remote_playlist",
        "playlist_builder.ui.shared.dto",  # transitional — provider_auth uses ProviderAuthState
    )
    for path in sorted(root.glob("*.py")):
        if path.name == "__init__.py":
            continue
        for module in _collect_import_modules(path):
            if not module.startswith("playlist_builder.ui"):
                continue
            if any(module.startswith(prefix) for prefix in allowed_ui_prefixes):
                continue
            raise AssertionError(f"{path} imports UI module {module} — use domain types instead")


def test_playlist_sync_core_does_not_import_integration_providers() -> None:
    """Sync planning/conflicts stay provider-blind (extends test_sync_architecture)."""
    root = Path("playlist_builder/app/playlist_sync")
    forbidden_tokens = ("integration.apple_music", "integration.youtube_music")
    skip_files = {"action_executor.py", "apply.py"}  # apply layer may reference ports
    for path in sorted(root.glob("*.py")):
        if path.name in skip_files:
            continue
        for module in _collect_import_modules(path):
            if any(token in module for token in forbidden_tokens):
                raise AssertionError(f"{path} imports provider module {module}")


def test_observability_does_not_import_bridge_runtime() -> None:
    """Observability should remain usable without the bridge god object."""
    root = Path("playlist_builder/observability")
    forbidden = "bridge_runtime"
    for path in sorted(root.glob("*.py")):
        for module in _collect_import_modules(path):
            if forbidden in module:
                raise AssertionError(f"{path} imports bridge_runtime ({module})")
