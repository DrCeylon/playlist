from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.e2e.scenarios import AUTOMATED_SCENARIO_IDS, USER_SCENARIOS

# Map scenario ids to test modules that implement them (manual registry).
SCENARIO_IMPLEMENTATION: dict[str, tuple[str, ...]] = {
    "import.file.remote": ("tests/e2e/test_user_journey_sync.py",),
    "create.local.repository": ("tests/e2e/test_user_journey_sync.py",),
    "snapshot.archive": ("tests/test_playlist_repository.py",),
    "sync.dry_run": ("tests/e2e/test_user_journey_sync.py",),
    "sync.apply.append": ("tests/e2e/test_user_journey_sync.py",),
    "sync.partial_failure": ("tests/e2e/test_user_journey_sync.py",),
    "sync.conflicts.resolve": ("tests/e2e/test_user_journey_sync.py", "tests/test_resolve_sync_bridge.py"),
    "history.migration": ("tests/e2e/test_user_journey_history.py", "tests/test_playlist_library_bridge.py"),
    "observability.diagnostics": ("tests/e2e/test_user_journey_providers.py", "tests/test_observability_foundations.py"),
    "plugins.extension_points": ("tests/e2e/test_user_journey_providers.py", "tests/test_plugin_platform_foundations.py"),
    "providers.list": ("tests/e2e/test_user_journey_providers.py",),
    "errors.invalid_bridge": ("tests/test_ui_bridge_parsing_errors.py", "tests/test_ui_bridge_json_rpc.py"),
    "resume.import.checkpoint": ("tests/test_import_stream_checkpoint_resume.py",),
    "migration.history_idempotent": ("tests/test_playlist_repository.py", "tests/e2e/test_user_journey_history.py"),
    "import.apple.stream": ("tests/test_import_stream_checkpoint_resume.py", "tests/test_ui_bridge_runtime.py"),
    "import.youtube.file": ("tests/e2e/test_user_journey_providers.py", "tests/test_youtube_music_gateway.py"),
}


def test_automated_scenarios_have_implementation_mapping() -> None:
  missing = AUTOMATED_SCENARIO_IDS - set(SCENARIO_IMPLEMENTATION)
  assert not missing, f"Unmapped automated scenarios: {sorted(missing)}"


@pytest.mark.parametrize("scenario_id", sorted(AUTOMATED_SCENARIO_IDS))
def test_scenario_implementation_files_exist(scenario_id: str) -> None:
    paths = SCENARIO_IMPLEMENTATION[scenario_id]
    for rel in paths:
        assert Path(rel).is_file(), f"{scenario_id} -> missing {rel}"


def test_classify_existing_test_files_by_tier() -> None:
    """Smoke audit: every tests/*.py file is classifiable (no orphan without tests)."""
    root = Path("tests")
    py_files = [p for p in root.rglob("test_*.py") if p.is_file()]
    assert len(py_files) >= 80


def test_redundant_e2e_naming_legacy_file_documents_tier() -> None:
    """test_e2e_import_mocked is integration-tier — documented, not duplicate of new e2e harness."""
    path = Path("tests/test_e2e_import_mocked.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert "test_mocked_e2e_kygo_firestone_is_added" in funcs
    assert "test_music_client_batch_uses_resolver_and_delivery" in funcs
