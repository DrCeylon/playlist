#!/usr/bin/env python3
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass

MIN_PYTHON = (3, 12)


@dataclass(frozen=True, slots=True)
class EnvironmentCheckResult:
    ok: bool
    message: str


def validate_python_version(version_info: tuple[int, int, int]) -> EnvironmentCheckResult:
    if version_info >= (*MIN_PYTHON, 0):
        return EnvironmentCheckResult(ok=True, message=f"Python {version_info[0]}.{version_info[1]}.{version_info[2]} OK")
    return EnvironmentCheckResult(
        ok=False,
        message=(
            "Python 3.12+ is required for this project "
            "(uses StrEnum and dataclass(slots=True)). "
            f"Detected {version_info[0]}.{version_info[1]}.{version_info[2]}."
        ),
    )


def main() -> int:
    py_check = validate_python_version((sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
    if not py_check.ok:
        print(f"error: {py_check.message}", file=sys.stderr)
        print("hint: install Python 3.12 with Homebrew and recreate your venv:", file=sys.stderr)
        print("      brew install python@3.12", file=sys.stderr)
        print("      python3.12 -m venv .venv && source .venv/bin/activate", file=sys.stderr)
        return 1
    print(f"ok: {py_check.message}")

    if platform.system() == "Darwin":
        xcode_path = shutil.which("xcodebuild")
        if not xcode_path:
            print("warning: xcodebuild not found; Swift tests may fail (install Xcode).")
        else:
            print(f"ok: Xcode toolchain detected at {xcode_path}")
        if shutil.which("xcode-select"):
            try:
                selected = subprocess.check_output(["xcode-select", "-p"], text=True).strip()
                print(f"ok: xcode-select path = {selected}")
            except subprocess.CalledProcessError:
                print("warning: xcode-select is installed but returned an error.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

