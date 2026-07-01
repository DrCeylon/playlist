#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v swift >/dev/null 2>&1; then
  echo "error: Swift toolchain not found" >&2
  exit 1
fi

echo "==> swift build"
swift build

echo "==> swift test"
swift test

echo "==> Resonance package OK"
