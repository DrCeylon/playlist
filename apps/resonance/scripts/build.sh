#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v swift >/dev/null 2>&1; then
  echo "error: Swift toolchain not found" >&2
  echo "hint: install Xcode (or Xcode Command Line Tools) and ensure swift is on PATH" >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  if ! command -v xcode-select >/dev/null 2>&1; then
    echo "error: xcode-select not found; install Xcode Command Line Tools." >&2
    exit 1
  fi
  if ! xcode-select -p >/dev/null 2>&1; then
    echo "error: xcode-select has no active developer directory." >&2
    echo "hint: sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer" >&2
    exit 1
  fi
  if ! xcrun --find xctest >/dev/null 2>&1; then
    echo "error: XCTest runtime not found (no such module 'XCTest' likely)." >&2
    echo "hint: install full Xcode and run: sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer" >&2
    exit 1
  fi
fi

echo "==> swift build"
swift build

echo "==> swift test"
swift test

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo ""
  echo "Tip: build a proper .app with icon for Finder/Dock:"
  echo "  ./scripts/package-mac-app.sh"
  echo "  open dist/ResonanceMac.app"
fi

echo "==> Resonance package OK"
