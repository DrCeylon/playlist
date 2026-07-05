"""Unit tests for Phase 5.3 performance tracing."""

from __future__ import annotations

import json
import os
from io import StringIO

import pytest

from playlist_builder.infrastructure.perf.trace import (
    ENV_PERF_TRACE,
    PerfSession,
    perf_record,
    perf_span,
    perf_trace_enabled,
)
from playlist_builder.reports.perf_report import render_baseline_markdown, write_perf_json


def test_perf_trace_disabled_by_default(monkeypatch, capsys):
    monkeypatch.delenv(ENV_PERF_TRACE, raising=False)
    perf_record("bridge", "context_build", 42)
    captured = capsys.readouterr()
    assert "resonance-perf:" not in captured.err


def test_perf_trace_emits_structured_stderr(monkeypatch, capsys):
    monkeypatch.setenv(ENV_PERF_TRACE, "1")
    assert perf_trace_enabled()
    with perf_span("bridge", "context_build"):
        pass
    captured = capsys.readouterr()
    assert "resonance-perf:" in captured.err
    payload_line = next(line for line in captured.err.splitlines() if line.startswith("resonance-perf:"))
    payload = json.loads(payload_line.removeprefix("resonance-perf: ").strip())
    assert payload["phase"] == "bridge"
    assert payload["operation"] == "context_build"
    assert payload["duration_ms"] >= 0


def test_perf_session_collects_spans_without_stderr(monkeypatch, capsys):
    monkeypatch.delenv(ENV_PERF_TRACE, raising=False)
    with PerfSession(scenario="S1", operation="import", track_count=10, cache_mode="cold") as session:
        perf_record("import", "resolve_total", 1200, metadata={"track_count": 10})
        perf_record("delivery", "delivery_batch", 800, batch_index=1)
    captured = capsys.readouterr()
    assert "resonance-perf:" not in captured.err
    assert len(session.spans) == 2
    tops = session.top_operations(2)
    assert tops[0][0] == "import.resolve_total"
    assert tops[0][1] == 1200


def test_write_perf_json(tmp_path):
    with PerfSession(scenario="S1", operation="import", track_count=10, cache_mode="cold") as session:
        perf_record("import", "import_total", 5000)
    path = write_perf_json(session, tmp_path, stem="import")
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["scenario"] == "S1"
    assert payload["track_count"] == 10
    assert payload["summary_by_operation"]["import.import_total"] == 5000


def test_render_baseline_markdown_includes_top_three():
    runs = [
        {
            "scenario": "S1",
            "track_count": 10,
            "cache_mode": "cold",
            "total_duration_ms": 45000,
            "summary_by_operation": {
                "import.delivery_total": 20000,
                "import.resolve_total": 15000,
                "bridge.python_cold_start": 1800,
            },
            "top_operations": [
                {"operation": "import.delivery_total", "duration_ms": 20000},
                {"operation": "import.resolve_total", "duration_ms": 15000},
                {"operation": "bridge.python_cold_start", "duration_ms": 1800},
            ],
        }
    ]
    markdown = render_baseline_markdown(runs, machine_label="MacBook Pro M3")
    assert "Phase 5.3 — Rapport baseline performance" in markdown
    assert "import.delivery_total" in markdown
    assert "MacBook Pro M3" in markdown
    assert "MusicKit REST" in markdown
