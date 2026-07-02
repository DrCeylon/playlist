from __future__ import annotations

import sys

import pytest


def pytest_sessionstart(session: pytest.Session) -> None:
    if sys.version_info < (3, 12):
        raise pytest.UsageError(
            "Python 3.12+ is required for this repository "
            "(uses StrEnum and dataclass(slots=True)). "
            f"Detected {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}."
        )

