from __future__ import annotations

import json
from pathlib import Path

import pytest

from playlist_builder.ui.bridge.commands import playlist_generation_request_from_dict
from playlist_builder.ui.shared.validation.generation import validate_playlist_generation_request

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "playlist_generation_request.json"

REQUIRED_BUILDER_SWIFT_PATHS = (
    REPO_ROOT / "apps" / "resonance" / "ResonanceCore" / "Sources" / "ResonanceCore" / "Validation.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceCore" / "Sources" / "ResonanceCore" / "BridgeContracts.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceCore" / "Sources" / "ResonanceCore" / "BridgeClient.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceCore" / "Sources" / "ResonanceCore" / "ImportModels.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceMac" / "Sources" / "ResonanceMac" / "Services" / "PythonEngineBridgeService.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceMac" / "Sources" / "ResonanceMac" / "ViewModels" / "ImportViewModel.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceMac" / "Sources" / "ResonanceMac" / "Screens" / "PlaylistBuilderView.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceMac" / "Sources" / "ResonanceMac" / "Screens" / "PlaylistPreviewView.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceMac" / "Sources" / "ResonanceMac" / "Screens" / "ImportProgressView.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceMac" / "Sources" / "ResonanceMac" / "Screens" / "ImportReportView.swift",
    REPO_ROOT / "apps" / "resonance" / "ResonanceMac" / "Sources" / "ResonanceMac" / "ViewModels" / "PlaylistBuilderViewModel.swift",
)


def test_playlist_builder_swift_files_exist():
    missing = [str(path.relative_to(REPO_ROOT)) for path in REQUIRED_BUILDER_SWIFT_PATHS if not path.is_file()]
    assert missing == []


def test_bridge_fixture_validates_with_python_contract():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    request = playlist_generation_request_from_dict(payload)
    result = validate_playlist_generation_request(request)
    assert result.is_valid, result.errors


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("name", "Le nom de la playlist est obligatoire."),
        ("seeds", "Au moins une graine (artiste/morceau) ou un mot-clé est requis."),
        ("target_track_count", "Le nombre de morceaux ou la durée cible est requis."),
    ],
)
def test_python_validation_messages_match_phase_41_contract(field: str, message: str):
  payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
  broken = dict(payload)
  if field == "name":
      broken["name"] = "   "
  elif field == "seeds":
      broken["seeds"] = []
      broken["keywords"] = []
  elif field == "target_track_count":
      broken["target_track_count"] = None
      broken["target_duration_minutes"] = None
  request = playlist_generation_request_from_dict(broken)
  result = validate_playlist_generation_request(request)
  assert not result.is_valid
  assert any(error.field == field and error.message == message for error in result.errors)
