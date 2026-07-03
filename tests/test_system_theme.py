"""Tests for system theme resolution."""

from playlist_builder.ui.shared.theme.manager import (
    DARK_THEME_ID,
    LIGHT_THEME_ID,
    SYSTEM_THEME_ID,
    resolve_theme_id,
)


def test_system_resolves_light_and_dark() -> None:
    assert resolve_theme_id(SYSTEM_THEME_ID, dark=False) == LIGHT_THEME_ID
    assert resolve_theme_id(SYSTEM_THEME_ID, dark=True) == DARK_THEME_ID


def test_manual_theme_is_not_affected_by_dark_flag() -> None:
    assert resolve_theme_id("classic_winamp_inspired", dark=True) == "classic_winamp_inspired"
