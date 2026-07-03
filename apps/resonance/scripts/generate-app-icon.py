#!/usr/bin/env python3
"""Generate macOS AppIcon assets: square 1024 master, transparent background, iconset."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CANDIDATES = (
    ROOT / "ResonanceMac/Resources/Assets/AppIcon-source.png",
    ROOT / "ResonanceMac/Resources/Assets/AppIcon-1024.png",
)
MASTER = ROOT / "ResonanceMac/Resources/Assets/AppIcon-1024.png"
ICONSET = ROOT / "ResonanceMac/Resources/AppIcon.iconset"
CANVAS_SIZE = 1024
WHITE_THRESHOLD = 245

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


def _load_source() -> Image.Image:
    for candidate in SOURCE_CANDIDATES:
        if candidate.exists():
            return Image.open(candidate).convert("RGBA")
    raise SystemExit(
        "Master icon missing. Expected one of:\n"
        + "\n".join(f"  - {path}" for path in SOURCE_CANDIDATES)
    )


def _remove_near_white_background(image: Image.Image) -> Image.Image:
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            if red >= WHITE_THRESHOLD and green >= WHITE_THRESHOLD and blue >= WHITE_THRESHOLD:
                pixels[x, y] = (red, green, blue, 0)
    return image


def _compose_square_master(image: Image.Image, *, canvas_size: int = CANVAS_SIZE) -> Image.Image:
    bbox = image.getbbox()
    if bbox is None:
        raise SystemExit("Icon source has no visible pixels after background removal.")

    content = image.crop(bbox)
    content_width, content_height = content.size
    max_edge = max(content_width, content_height)
    scale = canvas_size / max_edge
    target_width = max(1, int(round(content_width * scale)))
    target_height = max(1, int(round(content_height * scale)))
    resized = content.resize((target_width, target_height), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    offset_x = (canvas_size - target_width) // 2
    offset_y = (canvas_size - target_height) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    return canvas


def prepare_master() -> Image.Image:
    source = _load_source()
    cleaned = _remove_near_white_background(source)
    return _compose_square_master(cleaned)


def main() -> None:
    master = prepare_master()
    if master.size != (CANVAS_SIZE, CANVAS_SIZE):
        master = master.resize((CANVAS_SIZE, CANVAS_SIZE), Image.Resampling.LANCZOS)

    MASTER.parent.mkdir(parents=True, exist_ok=True)
    ICONSET.mkdir(parents=True, exist_ok=True)
    master.save(MASTER, format="PNG", optimize=True)

    for filename, size in SIZES.items():
        resized = master.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(ICONSET / filename, format="PNG", optimize=True)

    dock_icon = master.resize((512, 512), Image.Resampling.LANCZOS)
    dock_icon.save(ROOT / "ResonanceMac/Resources/Assets/AppIcon-512.png", format="PNG", optimize=True)
    print(f"Generated square transparent master at {MASTER}")
    print(f"Generated {len(SIZES)} iconset PNGs in {ICONSET}")


if __name__ == "__main__":
    main()
