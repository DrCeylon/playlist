from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RESONANCE_ROOT = REPO_ROOT / "apps" / "resonance"
PYTHON_THEMES = REPO_ROOT / "playlist_builder" / "ui" / "shared" / "theme" / "themes"
SWIFT_THEMES = (
    RESONANCE_ROOT
    / "ResonanceDesign"
    / "Sources"
    / "ResonanceDesign"
    / "Resources"
    / "themes"
)

REQUIRED_SWIFT_PATHS = (
    RESONANCE_ROOT / "Package.swift",
    RESONANCE_ROOT / "ResonanceCore" / "Sources" / "ResonanceCore" / "AppRoute.swift",
    RESONANCE_ROOT / "ResonanceDesign" / "Sources" / "ResonanceDesign" / "ThemeManager.swift",
    RESONANCE_ROOT / "ResonanceMac" / "Sources" / "ResonanceMac" / "ResonanceMacApp.swift",
    RESONANCE_ROOT / "ResonanceMac" / "Sources" / "ResonanceMac" / "AppShellView.swift",
    RESONANCE_ROOT / "ResonanceMac" / "Sources" / "ResonanceMac" / "HomeView.swift",
    RESONANCE_ROOT / "ResonanceMac" / "Sources" / "ResonanceMac" / "SettingsView.swift",
)

BUNDLED_THEME_IDS = (
    "apple_music_light",
    "apple_music_dark",
    "classic_winamp_inspired",
)

FORBIDDEN_SWIFT_PATTERNS = (
    "NSAppleScript",
    "AppleScript",
    "playlist_builder.integration.apple_music",
    "MusicKit",
    "deletePlaylist",
    "deleteLibrary",
    "removePlaylist",
)

SWIFT_UI_ROOTS = (
    RESONANCE_ROOT / "ResonanceMac" / "Sources",
    RESONANCE_ROOT / "ResonanceDesign" / "Sources",
)

HEX_COLOR_PATTERN = re.compile(r"#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?")

SWIFT_AVAILABLE = shutil.which("swift") is not None


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_resonance_package_structure_exists():
    missing = [str(path.relative_to(REPO_ROOT)) for path in REQUIRED_SWIFT_PATHS if not path.is_file()]
    assert missing == []


@pytest.mark.parametrize("theme_id", BUNDLED_THEME_IDS)
def test_bundled_theme_json_present_in_swift_package(theme_id: str):
    path = SWIFT_THEMES / f"{theme_id}.theme.json"
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["id"] == theme_id


@pytest.mark.parametrize("theme_id", BUNDLED_THEME_IDS)
def test_swift_theme_json_matches_python_source(theme_id: str):
    python_path = PYTHON_THEMES / f"{theme_id}.theme.json"
    swift_path = SWIFT_THEMES / f"{theme_id}.theme.json"
    assert _file_hash(python_path) == _file_hash(swift_path)


def test_swift_ui_has_no_forbidden_patterns():
    offenders: list[str] = []
    for root in SWIFT_UI_ROOTS:
        for path in root.rglob("*.swift"):
            text = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_SWIFT_PATTERNS:
                if pattern in text:
                    offenders.append(f"{path.relative_to(REPO_ROOT)} contains {pattern!r}")
    assert offenders == []


def test_swift_ui_views_have_no_hardcoded_hex_colors():
    offenders: list[str] = []
    mac_sources = RESONANCE_ROOT / "ResonanceMac" / "Sources"
    for path in mac_sources.rglob("*.swift"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "Color(hex:" in line or "tokenHex:" in line:
                continue
            if HEX_COLOR_PATTERN.search(line):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{line_number}: {line.strip()}")
    assert offenders == []


@pytest.mark.skipif(not SWIFT_AVAILABLE, reason="Swift toolchain not available")
def test_swift_package_build_and_tests():
    result = subprocess.run(
        ["bash", str(RESONANCE_ROOT / "scripts" / "build.sh")],
        cwd=RESONANCE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
