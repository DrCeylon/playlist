from __future__ import annotations

import re
from pathlib import Path

import pytest

from playlist_builder.ui.shared.dto.theme import ThemeOption
from playlist_builder.ui.shared.theme import (
    DesignTokens,
    SYSTEM_THEME_ID,
    Theme,
    ThemeLoadError,
    ThemeManager,
    ThemeNotFoundError,
    ThemeRegistry,
    ThemeValidationError,
    resolve_theme_id,
    theme_to_option,
    validate_theme,
)
from playlist_builder.ui.shared.theme.loader import load_theme_file, resolve_definitions
from playlist_builder.ui.shared.theme.contrast import (
    MINIMUM_CONTRAST_RATIO,
    contrast_ratio,
    has_readable_contrast,
)
from playlist_builder.ui.shared.theme.tokens import DesignTokens as TokensClass
from playlist_builder.ui.shared.theme.validation import is_valid_color

BUNDLED_THEME_IDS = (
    "apple_music_light",
    "apple_music_dark",
    "classic_winamp_inspired",
)


def test_all_bundled_themes_load():
    registry = ThemeRegistry.load_bundled()
    loaded_ids = {theme.id for theme in registry.list()}
    assert loaded_ids == set(BUNDLED_THEME_IDS)


def test_all_bundled_themes_validate():
    registry = ThemeRegistry.load_bundled()
    for theme in registry.list():
        report = registry.validate(theme)
        assert report.result.is_valid, report.result.errors


@pytest.mark.parametrize("theme_id", BUNDLED_THEME_IDS)
def test_bundled_theme_get(theme_id: str):
    registry = ThemeRegistry.load_bundled()
    theme = registry.get(theme_id)
    assert theme.id == theme_id
    assert theme.tokens.colors["color.background.primary"]


def test_unknown_theme_raises_controlled_error():
    registry = ThemeRegistry.load_bundled()
    with pytest.raises(ThemeNotFoundError, match="inconnu"):
        registry.get("does_not_exist")


def test_theme_manager_apply_unknown_theme_raises():
    registry = ThemeRegistry.load_bundled()
    manager = ThemeManager(registry)
    with pytest.raises(ThemeNotFoundError):
        manager.apply("does_not_exist")


def test_inheritance_merges_parent_and_child_tokens():
    registry = ThemeRegistry.load_bundled()
    parent = registry.get("apple_music_dark")
    child = registry.get("classic_winamp_inspired")

    assert child.extends == "apple_music_dark"
    assert child.tokens.colors["color.background.primary"] == "#232323"
    assert child.tokens.colors["color.text.primary"] == "#E8FFE8"
    assert child.tokens.colors["color.accent.primary"] == "#00FF99"
    assert child.tokens.spacing["space.md"] == parent.tokens.spacing["space.md"]


@pytest.mark.parametrize("theme_id", BUNDLED_THEME_IDS)
def test_bundled_themes_have_readable_contrast(theme_id: str):
    registry = ThemeRegistry.load_bundled()
    theme = registry.get(theme_id)
    colors = theme.tokens.colors
    background = colors["color.background.primary"]
    surface = colors.get("color.surface", colors["color.background.secondary"])
    text_primary = colors["color.text.primary"]
    input_background = colors.get("color.input.background", colors["color.background.elevated"])
    input_text = colors.get("color.input.text", colors["color.text.primary"])
    warning = colors["color.status.warning"]
    error = colors["color.status.error"]

    assert has_readable_contrast(text_primary, background), f"{theme_id}: textPrimary vs background"
    assert has_readable_contrast(text_primary, surface), f"{theme_id}: textPrimary vs surface"
    assert has_readable_contrast(input_text, input_background), f"{theme_id}: inputText vs inputBackground"
    assert has_readable_contrast(warning, background), (
        f"{theme_id}: warning vs background ({contrast_ratio(warning, background):.3f} < {MINIMUM_CONTRAST_RATIO})"
    )
    assert has_readable_contrast(error, background), (
        f"{theme_id}: error vs background ({contrast_ratio(error, background):.3f} < {MINIMUM_CONTRAST_RATIO})"
    )
    text_secondary = colors["color.text.secondary"]
    text_tertiary = colors["color.text.tertiary"]
    assert has_readable_contrast(text_secondary, background), (
        f"{theme_id}: textSecondary vs background ({contrast_ratio(text_secondary, background):.3f})"
    )
    assert has_readable_contrast(text_tertiary, surface), (
        f"{theme_id}: textTertiary vs surface ({contrast_ratio(text_tertiary, surface):.3f})"
    )


def test_theme_manager_notifies_subscribers_on_apply():
    registry = ThemeRegistry.load_bundled()
    manager = ThemeManager(registry)
    seen: list[str] = []
    manager.subscribe(lambda theme: seen.append(theme.id))

    manager.apply("apple_music_dark")
    assert seen == ["apple_music_dark"]

    manager.apply("apple_music_dark")
    assert seen == ["apple_music_dark"]

    manager.apply("classic_winamp_inspired")
    assert seen == ["apple_music_dark", "classic_winamp_inspired"]


def test_theme_manager_unsubscribe_stops_notifications():
    registry = ThemeRegistry.load_bundled()
    manager = ThemeManager(registry)
    seen: list[str] = []

    def on_theme_change(theme: Theme) -> None:
        seen.append(theme.id)

    manager.subscribe(on_theme_change)
    manager.apply("apple_music_dark")
    assert seen == ["apple_music_dark"]

    manager.unsubscribe(on_theme_change)
    manager.apply("classic_winamp_inspired")
    assert seen == ["apple_music_dark"]


def test_theme_manager_active_defaults_to_system_light() -> None:
    registry = ThemeRegistry.load_bundled()
    manager = ThemeManager(registry)
    assert manager.selected_theme_id == SYSTEM_THEME_ID
    assert manager.active.id == "apple_music_light"


def test_theme_manager_system_follows_dark_flag() -> None:
    registry = ThemeRegistry.load_bundled()
    manager = ThemeManager(registry, default_theme_id=SYSTEM_THEME_ID, dark=True)
    assert manager.active.id == "apple_music_dark"
    manager.set_dark(False)
    assert manager.active.id == "apple_music_light"


def test_resolve_theme_id_manual_choice() -> None:
    assert resolve_theme_id("apple_music_dark", dark=False) == "apple_music_dark"


def test_theme_to_option_mapping():
    registry = ThemeRegistry.load_bundled()
    theme = registry.get("apple_music_dark")
    option = theme_to_option(theme)

    assert option == ThemeOption(
        theme_id="apple_music_dark",
        display_name="Apple Music Dark",
        preview_background="#1C1C1E",
        preview_accent="#FA2D48",
    )


def test_design_tokens_merge():
    base = DesignTokens(
        colors={"color.background.primary": "#111111"},
        typography={"font.body": "15,regular"},
        spacing={"space.md": 16},
        radius={"radius.md": 10},
        shadows={"shadow.card": "0 1px 2px #00000010"},
    )
    override = DesignTokens(
        colors={"color.accent.primary": "#00FF99"},
        typography={},
        spacing={},
        radius={},
        shadows={},
    )
    merged = base.merge(override)
    assert merged.colors["color.background.primary"] == "#111111"
    assert merged.colors["color.accent.primary"] == "#00FF99"
    assert merged.typography["font.body"] == "15,regular"


def test_validate_theme_rejects_invalid_color():
    theme = Theme(
        id="broken",
        display_name="Broken",
        version="1.0.0",
        tokens=DesignTokens(
            colors={"color.background.primary": "red"},
            typography={key: "12,regular" for key in (
                "font.largeTitle",
                "font.title",
                "font.headline",
                "font.body",
                "font.callout",
                "font.caption",
                "font.mono",
            )},
            spacing={key: 8 for key in ("space.xs", "space.sm", "space.md", "space.lg", "space.xl", "space.xxl")},
            radius={key: 8 for key in ("radius.sm", "radius.md", "radius.lg", "radius.xl")},
            shadows={"shadow.card": "0 1px 2px #00000010", "shadow.elevated": "0 2px 4px #00000020"},
        ),
    )
    result = validate_theme(theme)
    assert not result.is_valid


def test_validate_theme_rejects_negative_spacing():
    registry = ThemeRegistry.load_bundled()
    base = registry.get("apple_music_light")
    broken = Theme(
        id="broken_spacing",
        display_name="Broken",
        version="1.0.0",
        tokens=DesignTokens(
            colors=dict(base.tokens.colors),
            typography=dict(base.tokens.typography),
            spacing={**base.tokens.spacing, "space.md": -1},
            radius=dict(base.tokens.radius),
            shadows=dict(base.tokens.shadows),
        ),
    )
    result = validate_theme(broken)
    assert not result.is_valid


def test_register_invalid_theme_raises_validation_error():
    registry = ThemeRegistry()
    theme = Theme(
        id="",
        display_name="Broken",
        version="",
        tokens=TokensClass.empty(),
    )
    with pytest.raises(ThemeValidationError):
        registry.register(theme)


def test_circular_inheritance_raises_load_error():
    left = {
        "id": "left",
        "displayName": "Left",
        "version": "1.0.0",
        "extends": "right",
        "tokens": {"colors": {"color.background.primary": "#111111"}},
    }
    right = {
        "id": "right",
        "displayName": "Right",
        "version": "1.0.0",
        "extends": "left",
        "tokens": {"colors": {"color.background.primary": "#222222"}},
    }
    from playlist_builder.ui.shared.theme.loader import parse_theme_definition

    definitions = (
        parse_theme_definition(left),
        parse_theme_definition(right),
    )
    with pytest.raises(ThemeLoadError, match="circulaire"):
        resolve_definitions(definitions)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("#AABBCC", True),
        ("#123456", True),
        ("#12345678", True),
        ("#abcdef", True),
        ("red", False),
        ("#12345", False),
        ("#GGGGGG", False),
    ],
)
def test_is_valid_color(value: str, expected: bool):
    assert is_valid_color(value) is expected


def test_theme_engine_python_files_have_no_hardcoded_colors():
    theme_root = Path(__file__).resolve().parents[1] / "playlist_builder" / "ui" / "shared" / "theme"
    color_pattern = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
    offenders: list[str] = []
    for path in theme_root.rglob("*.py"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "re.compile" in line or "_COLOR_PATTERN" in line:
                continue
            if color_pattern.search(line):
                offenders.append(f"{path.name}:{line_number}: {line.strip()}")
    assert offenders == []


def test_theme_engine_has_no_provider_specific_imports():
    theme_root = Path(__file__).resolve().parents[1] / "playlist_builder" / "ui" / "shared" / "theme"
    forbidden_prefixes = (
        "playlist_builder.integration.apple_music",
        "playlist_builder.core.applescript",
        "playlist_builder.app.factory",
    )
    offenders: list[str] = []
    for path in theme_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for prefix in forbidden_prefixes:
            if prefix in text:
                offenders.append(f"{path.name} references {prefix}")
    assert offenders == []


def test_load_theme_file_rejects_invalid_json(tmp_path: Path):
    path = tmp_path / "broken.theme.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ThemeLoadError, match="JSON invalide"):
        load_theme_file(path)
