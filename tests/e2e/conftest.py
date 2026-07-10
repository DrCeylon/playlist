from __future__ import annotations

from pathlib import Path

import pytest

from tests.e2e.harness import E2EHarness, build_e2e_harness


@pytest.fixture
def e2e_harness(tmp_path: Path) -> E2EHarness:
    return build_e2e_harness(tmp_path)
