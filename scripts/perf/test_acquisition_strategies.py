#!/usr/bin/env python3
"""Phase 5.3.3 — macOS acquisition strategy experiments (explicit manual launch only).

This script is NOT integrated into Resonance runtime. Run it manually on macOS
with a track that is not yet present in your local Music.app library.

Example:
  python3.12 scripts/perf/test_acquisition_strategies.py \\
    --url "https://music.apple.com/us/song/example/1234567890" \\
    --track-id 1234567890 \\
    --artist "Artist" \\
    --title "Title" \\
    --strategies S1,S2,S3,S4 \\
    --machine "MacBook Pro M3"
"""

from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from playlist_builder.integration.apple_music.acquisition_experiments import (
    AcquisitionExperimentInput,
    AcquisitionStrategyId,
    default_search_terms,
    run_acquisition_experiment,
    summarize_results,
)
from playlist_builder.reports.acquisition_strategy_report import write_acquisition_strategy_reports

STRATEGY_ALIASES = {
    "S1": AcquisitionStrategyId.ADD_URL_DIRECT,
    "S1_add_url_direct": AcquisitionStrategyId.ADD_URL_DIRECT,
    "S2": AcquisitionStrategyId.OPEN_LOCATION_APPLESCRIPT,
    "S2_open_location_applescript": AcquisitionStrategyId.OPEN_LOCATION_APPLESCRIPT,
    "S3": AcquisitionStrategyId.SYSTEM_EVENTS_ADD_TO_LIBRARY,
    "S3_system_events_add_to_library": AcquisitionStrategyId.SYSTEM_EVENTS_ADD_TO_LIBRARY,
    "S4": AcquisitionStrategyId.MANUAL_FALLBACK,
    "S4_manual_fallback": AcquisitionStrategyId.MANUAL_FALLBACK,
}


def _parse_strategies(raw: str) -> list[AcquisitionStrategyId]:
    items = [part.strip() for part in raw.split(",") if part.strip()]
    if not items:
        return list(AcquisitionStrategyId)
    parsed: list[AcquisitionStrategyId] = []
    for item in items:
        key = item.strip()
        if key not in STRATEGY_ALIASES:
            raise ValueError(f"Stratégie inconnue: {item!r}. Valeurs: {', '.join(sorted(STRATEGY_ALIASES))}")
        parsed.append(STRATEGY_ALIASES[key])
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 5.3.3 acquisition strategy experiments")
    parser.add_argument("--url", required=True, help="Apple Music catalog URL")
    parser.add_argument("--track-id", default="", help="iTunes/Apple Music track id")
    parser.add_argument("--artist", default="", help="Artist name for library search")
    parser.add_argument("--title", default="", help="Track title for library search")
    parser.add_argument(
        "--strategies",
        default="S1,S2,S3,S4",
        help="Comma-separated strategies: S1,S2,S3,S4",
    )
    parser.add_argument(
        "--reports-dir",
        default=str(REPO_ROOT / "reports" / "perf"),
        help="Output directory for JSON/Markdown reports",
    )
    parser.add_argument("--machine", default=platform.machine(), help="Machine label for the report")
    parser.add_argument(
        "--activate-music",
        action="store_true",
        help="Activate Music.app window for strategies that support background launch",
    )
    parser.add_argument(
        "--no-manual-prompt",
        action="store_true",
        help="Skip interactive Enter prompt for S4 manual fallback",
    )
    parser.add_argument(
        "--notes",
        default="Phase 5.3.3 explicit experiment — not part of Resonance product workflow.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if sys.platform != "darwin":
        print(
            "Ce script d'expérience nécessite macOS + Music.app. "
            "Lancez-le sur votre Mac, pas dans l'environnement CI/Linux.",
            file=sys.stderr,
        )
        return 2

    try:
        strategies = _parse_strategies(args.strategies)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    search_terms = default_search_terms(args.artist, args.title)
    experiment_input = AcquisitionExperimentInput(
        url=args.url,
        track_id=args.track_id,
        artist=args.artist,
        title=args.title,
        search_terms=search_terms,
        activate_music=bool(args.activate_music),
    )

    print("Phase 5.3.3 — acquisition strategy experiment", flush=True)
    print(f"Track: {args.artist} — {args.title}", flush=True)
    print(f"Strategies: {', '.join(strategy.value for strategy in strategies)}", flush=True)
    print("Ce script ne modifie pas le workflow Resonance.", flush=True)

    results = run_acquisition_experiment(
        experiment_input,
        strategies=strategies,
        manual_prompt=not args.no_manual_prompt,
    )
    summary = summarize_results(results)
    json_path, md_path = write_acquisition_strategy_reports(
        experiment_input=experiment_input,
        results=results,
        summary=summary,
        reports_dir=Path(args.reports_dir),
        machine_label=args.machine,
        notes=args.notes,
    )

    print("\nRésultats:", flush=True)
    for result in results:
        status = "OK" if result.success else "FAIL"
        print(
            f"  [{status}] {result.strategy_id} — {result.duration_ms} ms — "
            f"PID={result.persistent_id or '—'} — library={'yes' if result.found_in_library else 'no'}",
            flush=True,
        )
        if result.applescript_error:
            print(f"         error: {result.applescript_error}", flush=True)

    print(f"\nJSON: {json_path}", flush=True)
    print(f"Markdown: {md_path}", flush=True)
    return 0 if summary.get("success_count", 0) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
