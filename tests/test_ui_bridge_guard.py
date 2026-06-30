from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

import pytest

FORBIDDEN_IMPORT_PREFIXES = (
    "playlist_builder.integration.apple_music",
    "playlist_builder.core.applescript",
    "playlist_builder.app.factory",
)


def _collect_bridge_modules() -> list[str]:
    package_path = Path(__file__).resolve().parents[1] / "playlist_builder" / "ui" / "bridge"
    modules: list[str] = []
    for module_info in pkgutil.walk_packages([str(package_path)], prefix="playlist_builder.ui.bridge."):
        if module_info.ispkg:
            continue
        modules.append(module_info.name)
    return modules


def _forbidden_imports_in_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hits.extend(_match_forbidden(alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            hits.extend(_match_forbidden(node.module))
    return hits


def _match_forbidden(module_name: str) -> list[str]:
    return [module_name for prefix in FORBIDDEN_IMPORT_PREFIXES if module_name.startswith(prefix)]


@pytest.mark.parametrize("module_name", _collect_bridge_modules())
def test_bridge_module_imports_cleanly(module_name: str):
    importlib.import_module(module_name)


def test_bridge_packages_have_no_forbidden_imports():
    root = Path(__file__).resolve().parents[1] / "playlist_builder" / "ui" / "bridge"
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        hits = _forbidden_imports_in_file(path)
        for hit in hits:
            offenders.append(f"{path.name} imports {hit}")
    assert offenders == []
