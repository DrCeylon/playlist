#!/usr/bin/env bash
# Build ResonanceMac.app with icon for Finder/Dock (macOS only).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "error: packaging .app requires macOS (iconutil)." >&2
  exit 1
fi

APP_NAME="ResonanceMac"
DIST="$ROOT/dist"
APP_DIR="$DIST/$APP_NAME.app"
ICONSET="$ROOT/ResonanceMac/Resources/AppIcon.iconset"
INFO_PLIST="$ROOT/ResonanceMac/Resources/Info.plist"

if [[ ! -d "$ICONSET" ]]; then
  echo "==> generating AppIcon.iconset"
  python3 "$ROOT/scripts/generate-app-icon.py"
fi

echo "==> swift build -c release"
BIN_DIR="$(swift build -c release --show-bin-path)"
BINARY="$BIN_DIR/$APP_NAME"

echo "==> packaging $APP_DIR"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"

cp "$BINARY" "$APP_DIR/Contents/MacOS/$APP_NAME"
chmod +x "$APP_DIR/Contents/MacOS/$APP_NAME"
cp "$INFO_PLIST" "$APP_DIR/Contents/Info.plist"

iconutil -c icns "$ICONSET" -o "$APP_DIR/Contents/Resources/AppIcon.icns"

echo "==> ResonanceMac.app ready"
echo "    open \"$APP_DIR\""
