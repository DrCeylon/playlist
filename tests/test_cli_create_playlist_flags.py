from __future__ import annotations

import argparse

from playlist_builder.cli.create_playlist import build_parser


def test_default_engine_is_applescript():
    args = build_parser().parse_args([])
    assert args.engine == "applescript"


def test_no_wait_for_acquisition_is_documented():
    parser = build_parser()
    action = next(action for action in parser._actions if "--no-wait-for-acquisition" in action.option_strings)
    assert action.help is not None
    assert action.help != argparse.SUPPRESS


def test_wait_for_acquisition_enables_manual_mode():
    args = build_parser().parse_args(["--wait-for-acquisition"])
    assert args.wait_for_acquisition is True
    assert args.no_wait_for_acquisition is False


def test_no_wait_for_acquisition_overrides_manual_mode():
    args = build_parser().parse_args(["--wait-for-acquisition", "--no-wait-for-acquisition"])
    assert args.wait_for_acquisition is True
    assert args.no_wait_for_acquisition is True


def test_identity_cache_flag_accepts_custom_path(tmp_path):
    cache_path = tmp_path / "e2e_identity.json"
    args = build_parser().parse_args(["--identity-cache", str(cache_path)])
    assert args.identity_cache == cache_path


def test_json_diagnostics_flag():
    args = build_parser().parse_args(["--json-diagnostics"])
    assert args.json_diagnostics is True


def test_no_acquire_disables_catalog_acquisition():
    args = build_parser().parse_args(["--no-acquire"])
    assert args.no_acquire is True
