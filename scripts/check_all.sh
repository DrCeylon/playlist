#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> environment check"
python scripts/check_environment.py

echo "==> python tests"
python -m pytest -q

echo "==> resonance build"
(cd apps/resonance && ./scripts/build.sh)

echo "==> all checks passed"

