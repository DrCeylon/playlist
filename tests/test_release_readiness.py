from __future__ import annotations

import re
from pathlib import Path


def test_package_version_matches_pyproject() -> None:
    from playlist_builder import __version__

    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    assert match is not None
    assert __version__ == match.group(1)


def test_release_docs_exist() -> None:
    required = (
        "docs/README.md",
        "docs/RELEASE_PLAN.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/KNOWN_LIMITATIONS.md",
        "docs/MIGRATION_GUIDE.md",
        "docs/COMPATIBILITY_MATRIX.md",
        "docs/engineering/ENGINEERING_GUIDE.md",
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "SUPPORT.md",
        "AGENTS.md",
    )
    for path in required:
        assert Path(path).is_file(), f"missing {path}"
