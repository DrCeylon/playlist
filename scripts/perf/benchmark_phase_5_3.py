#!/usr/bin/env python3
"""Phase 5.3.1 benchmark runner — baseline collection (macOS required for import scenarios).

Usage:
  RESONANCE_PERF_TRACE=1 python3.12 scripts/perf/benchmark_phase_5_3.py --scenarios S1,S2,S3
  RESONANCE_PERF_TRACE=1 python3.12 scripts/perf/benchmark_phase_5_3.py --all --runs 3

Scenarios:
  S0  Bridge cold start (list_providers) — runs on any OS
  S1  Import 10 tracks, cache cold
  S2  Import 10 tracks, cache warm (repeat S1 playlist)
  S3  Import 30 tracks, cache cold
  S4  Import 80 tracks, cache cold
  G20 Generate 20 tracks
  G50 Generate 50 tracks
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from playlist_builder.infrastructure.perf.trace import ENV_PERF_TRACE, PerfSession, perf_record
from playlist_builder.reports.perf_report import write_baseline_markdown, write_perf_csv, write_perf_json


def _run_bridge_command(command: str, params: dict | None = None) -> tuple[int, int, list[str]]:
    payload = {
        "id": f"bench-{int(time.time() * 1000)}",
        "command": command,
        "params": params or {},
    }
    line = json.dumps(payload, ensure_ascii=False)
    started = time.perf_counter()
    env = os.environ.copy()
    env[ENV_PERF_TRACE] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    process = subprocess.run(
        [sys.executable, "-u", "-m", "playlist_builder.cli.engine_bridge"],
        input=line + "\n",
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=900,
    )
    duration_ms = int((time.perf_counter() - started) * 1000)
    stderr_lines = [item for item in process.stderr.splitlines() if item.startswith("resonance-perf:")]
    return process.returncode, duration_ms, stderr_lines


def benchmark_s0_cold_start() -> dict:
    with PerfSession(scenario="S0", operation="bridge_cold_start") as session:
        exit_code, duration_ms, stderr_lines = _run_bridge_command("list_providers")
        perf_record("bridge", "list_providers_round_trip", duration_ms, metadata={"exit_code": exit_code})
        for line in stderr_lines:
            try:
                payload = json.loads(line.removeprefix("resonance-perf: ").strip())
                perf_record(
                    payload.get("phase", "bridge"),
                    payload.get("operation", "unknown"),
                    int(payload.get("duration_ms", 0)),
                    metadata=payload.get("metadata", {}),
                )
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
    return session.to_report_payload()


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 5.3 baseline benchmarks")
    parser.add_argument("--scenarios", default="S0", help="Comma-separated scenario ids")
    parser.add_argument("--all", action="store_true", help="Run S0,G20,G50,S1,S2,S3,S4 (import requires macOS)")
    parser.add_argument("--runs", type=int, default=1, help="Repeat each scenario N times")
    parser.add_argument("--machine", default="", help="Machine label for the baseline report")
    parser.add_argument("--reports-dir", default=str(REPO_ROOT / "reports" / "perf"))
    args = parser.parse_args()

    os.environ[ENV_PERF_TRACE] = "1"
    reports_dir = Path(args.reports_dir)
    scenarios = (
        ["S0", "G20", "G50", "S1", "S2", "S3", "S4"]
        if args.all
        else [item.strip() for item in args.scenarios.split(",") if item.strip()]
    )

    collected_runs: list[dict] = []
    for scenario in scenarios:
        if scenario == "S0":
            for run_index in range(args.runs):
                payload = benchmark_s0_cold_start()
                payload["run_index"] = run_index + 1
                collected_runs.append(payload)
                write_perf_json(
                    _session_from_payload(payload),
                    reports_dir,
                    stem=f"bench_{scenario}_run{run_index + 1}",
                )
            continue

        if scenario.startswith(("S1", "S2", "S3", "S4", "G")):
            print(
                f"⚠️  Scenario {scenario} requires macOS + Music.app + fixture playlist. "
                "Run from Resonance app or extend this script with your fixture path.",
                file=sys.stderr,
            )
            continue

    if collected_runs:
        write_baseline_markdown(
            collected_runs,
            reports_dir,
            machine_label=args.machine,
            notes="Baseline partielle — compléter S1–S5 et G20/G50 sur macOS via l'app ou fixtures dédiées.",
        )
        print(f"Baseline report: {reports_dir / 'phase-5-3-baseline.md'}")
    else:
        print("No benchmark runs collected.", file=sys.stderr)
        return 1
    return 0


def _session_from_payload(payload: dict) -> PerfSession:
    session = PerfSession(
        scenario=str(payload.get("scenario", "")),
        operation=str(payload.get("operation", "")),
        track_count=payload.get("track_count"),
        cache_mode=str(payload.get("cache_mode", "")),
    )
    session.spans.extend([])
    return session


if __name__ == "__main__":
    raise SystemExit(main())
