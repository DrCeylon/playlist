from __future__ import annotations

from pathlib import Path

from PIL import Image

RESONANCE_ROOT = Path(__file__).resolve().parents[1] / "apps" / "resonance"
MASTER = RESONANCE_ROOT / "ResonanceMac/Resources/Assets/AppIcon-1024.png"
DOCK = RESONANCE_ROOT / "ResonanceMac/Resources/Assets/AppIcon-512.png"
ICONSET_MASTER = RESONANCE_ROOT / "ResonanceMac/Resources/AppIcon.iconset/icon_512x512@2x.png"


def _assert_square_transparent_corners(path: Path) -> None:
    image = Image.open(path).convert("RGBA")
    assert image.size[0] == image.size[1], f"{path.name} must be square, got {image.size}"
    width, height = image.size
    corners = (
        image.getpixel((0, 0)),
        image.getpixel((width - 1, 0)),
        image.getpixel((0, height - 1)),
        image.getpixel((width - 1, height - 1)),
    )
    assert all(alpha < 10 for *_, alpha in corners), f"{path.name} corners must be transparent"


def test_app_icon_master_is_square_with_transparent_corners() -> None:
    assert MASTER.exists(), "AppIcon-1024.png must exist"
    assert MASTER.stat().st_size > 0
    image = Image.open(MASTER).convert("RGBA")
    assert image.size == (1024, 1024)
    _assert_square_transparent_corners(MASTER)


def test_app_icon_dock_and_iconset_match_master_constraints() -> None:
    _assert_square_transparent_corners(DOCK)
    assert Image.open(DOCK).size == (512, 512)
    _assert_square_transparent_corners(ICONSET_MASTER)
    assert Image.open(ICONSET_MASTER).size == (1024, 1024)
