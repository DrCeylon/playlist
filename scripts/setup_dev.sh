#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "error: python3.12 not found."
  echo "hint: brew install python@3.12"
  exit 1
fi

if [[ ! -d .venv ]]; then
  echo "==> creating .venv with python3.12"
  python3.12 -m venv .venv
fi

echo "==> activating .venv"
source .venv/bin/activate

echo "==> upgrading pip"
python -m pip install --upgrade pip

echo "==> installing dev dependencies"
python -m pip install -e ".[dev]"
python -m pip install -r requirements-dev.txt

echo "==> checking environment"
python scripts/check_environment.py

echo "==> done. activate with: source .venv/bin/activate"

