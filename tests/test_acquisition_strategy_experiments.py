"""Tests for Phase 5.3.3 acquisition strategy experiments (reporting + parsing)."""

from __future__ import annotations

import json
import sys

import pytest

from playlist_builder.integration.apple_music.acquisition_experiments import (
    AcquisitionExperimentInput,
    AcquisitionStrategyId,
    AcquisitionStrategyResult,
    default_search_terms,
    summarize_results,
)
from playlist_builder.reports.acquisition_strategy_report import (
    render_acquisition_strategy_markdown,
    write_acquisition_strategy_reports,
)


def test_default_search_terms_deduplicates():
    terms = default_search_terms("Kygo", "Firestone")
    assert terms[0] == "Kygo Firestone"
    assert "Firestone" in terms
    assert len(terms) == len(set(term.casefold() for term in terms))


def test_summarize_results_prefers_fastest_success():
    results = [
        AcquisitionStrategyResult(
            strategy_id=AcquisitionStrategyId.ADD_URL_DIRECT.value,
            strategy_name="Add URL direct",
            success=True,
            duration_ms=1200,
            persistent_id="PID-1",
            found_in_library=True,
        ),
        AcquisitionStrategyResult(
            strategy_id=AcquisitionStrategyId.OPEN_LOCATION_APPLESCRIPT.value,
            strategy_name="Open duplicate",
            success=True,
            duration_ms=71000,
            persistent_id="PID-2",
            found_in_library=True,
        ),
        AcquisitionStrategyResult(
            strategy_id=AcquisitionStrategyId.SYSTEM_EVENTS_ADD_TO_LIBRARY.value,
            strategy_name="System Events",
            success=False,
            duration_ms=4000,
            applescript_error="-10006",
        ),
    ]
    summary = summarize_results(results)
    assert summary["success_count"] == 2
    assert summary["fastest_success"]["strategy_id"] == AcquisitionStrategyId.ADD_URL_DIRECT.value
    assert len(summary["failures"]) == 1


def test_write_acquisition_strategy_reports(tmp_path):
    experiment_input = AcquisitionExperimentInput(
        url="https://music.apple.com/us/song/firestone/950274258",
        track_id="950274258",
        artist="Kygo",
        title="Firestone",
        search_terms=("Kygo Firestone", "Firestone"),
    )
    results = [
        AcquisitionStrategyResult(
            strategy_id=AcquisitionStrategyId.MANUAL_FALLBACK.value,
            strategy_name="Fallback manuel",
            success=True,
            duration_ms=5000,
            persistent_id="PID-MANUAL",
            found_in_library=True,
            music_app_activated=True,
        )
    ]
    summary = summarize_results(results)
    json_path, md_path = write_acquisition_strategy_reports(
        experiment_input=experiment_input,
        results=results,
        summary=summary,
        reports_dir=tmp_path,
        machine_label="test-machine",
    )
    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["phase"] == "5.3.3"
    assert payload["results"][0]["persistent_id"] == "PID-MANUAL"
    markdown = md_path.read_text(encoding="utf-8")
    assert "Phase 5.3.3" in markdown
    assert "Fallback manuel" in markdown


def test_render_markdown_includes_failure_error():
    payload = {
        "generated_at": "2026-07-05T12:00:00",
        "machine_label": "Mac",
        "input": {"url": "https://example", "track_id": "1", "artist": "A", "title": "B"},
        "summary": {"strategy_count": 1, "success_count": 0, "fastest_success": None, "failures": []},
        "results": [
            {
                "strategy_name": "Open duplicate",
                "success": False,
                "duration_ms": 71000,
                "persistent_id": "",
                "found_in_library": False,
                "music_app_activated": False,
                "applescript_error": "duplicate: Can't set source Library (-10006)",
            }
        ],
    }
    markdown = render_acquisition_strategy_markdown(payload)
    assert "-10006" in markdown


def test_run_experiment_requires_macos():
    if sys.platform == "darwin":
        pytest.skip("macOS only guard test runs on non-macOS CI")
    from playlist_builder.integration.apple_music.acquisition_experiments import run_acquisition_experiment

    with pytest.raises(RuntimeError, match="macOS"):
        run_acquisition_experiment(
            AcquisitionExperimentInput(url="https://music.apple.com/song/id1", track_id="1")
        )
