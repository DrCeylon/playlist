#!/usr/bin/env python3
"""Generate macOS AppIcon.iconset PNGs from a 1024x1024 master."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "ResonanceMac/Resources/Assets/AppIcon-1024.png"
ICONSET = ROOT / "ResonanceMac/Resources/AppIcon.iconset"

SIZES: dict[str, int] = {
    "icon_16x16.png": 16,
    "icon_16x16@2x.png": 32,
    "icon_32x32.png": 32,
    "icon_32x32@2x.png": 64,
    "icon_128x128.png": 128,
    "icon_128x128@2x.png": 256,
    "icon_256x256.png": 256,
    "icon_256x256@2x.png": 512,
    "icon_512x512.png": 512,
    "icon_512x512@2x.png": 1024,
}


def main() -> None:
    if not MASTER.exists():
        raise SystemExit(f"Master icon missing: {MASTER}")

    ICONSET.mkdir(parents=True, exist_ok=True)
    source = Image.open(MASTER).convert("RGBA")
    if source.size != (1024, 1024):
        source = source.resize((1024, 1024), Image.Resampling.LANCZOS)

    for filename, size in SIZES.items():
        resized = source.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(ICONSET / filename, format="PNG", optimize=True)

    dock_icon = source.resize((512, 512), Image.Resampling.LANCZOS)
    dock_icon.save(ROOT / "ResonanceMac/Resources/Assets/AppIcon-512.png", format="PNG", optimize=True)
    print(f"Generated {len(SIZES)} iconset PNGs in {ICONSET}")


if __name__ == "__main__":
    main()
