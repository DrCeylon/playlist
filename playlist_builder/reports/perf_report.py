from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playlist_builder.infrastructure.perf.trace import PerfSession


def write_perf_json(session: PerfSession, reports_dir: Path, *, stem: str = "perf_trace") -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"{stem}_{timestamp}.json"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **session.to_report_payload(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_perf_csv(session: PerfSession, reports_dir: Path, *, stem: str = "perf_trace") -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = reports_dir / f"{stem}_{timestamp}.csv"
    fieldnames = [
        "phase",
        "operation",
        "duration_ms",
        "batch_index",
        "track_index",
        "cache_hit",
        "metadata_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for span in session.spans:
            writer.writerow(
                {
                    "phase": span.phase,
                    "operation": span.operation,
                    "duration_ms": span.duration_ms,
                    "batch_index": span.batch_index if span.batch_index is not None else "",
                    "track_index": span.track_index if span.track_index is not None else "",
                    "cache_hit": span.cache_hit if span.cache_hit is not None else "",
                    "metadata_json": json.dumps(span.metadata, ensure_ascii=False) if span.metadata else "",
                }
            )
    return path


def render_baseline_markdown(
    runs: list[dict[str, Any]],
    *,
    machine_label: str = "",
    notes: str = "",
) -> str:
    lines = [
        "# Phase 5.3 — Rapport baseline performance",
        "",
        f"*Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
    ]
    if machine_label:
        lines.extend([f"**Machine** : {machine_label}", ""])
    if notes:
        lines.extend([notes, ""])

    lines.extend(
        [
            "## Résumé des scénarios",
            "",
            "| Scénario | Morceaux | Cache | Total (ms) | Top 1 | Top 2 | Top 3 |",
            "|----------|----------|-------|------------|-------|-------|-------|",
        ]
    )

    aggregate_totals: dict[str, int] = {}
    for run in runs:
        summary = run.get("summary_by_operation", {})
        for key, value in summary.items():
            aggregate_totals[key] = aggregate_totals.get(key, 0) + int(value)
        tops = run.get("top_operations", [])[:3]
        while len(tops) < 3:
            tops.append({"operation": "—", "duration_ms": 0})
        lines.append(
            "| {scenario} | {track_count} | {cache_mode} | {total} | {t1} | {t2} | {t3} |".format(
                scenario=run.get("scenario", "—"),
                track_count=run.get("track_count", "—"),
                cache_mode=run.get("cache_mode", "—"),
                total=run.get("total_duration_ms", "—"),
                t1=f"{tops[0]['operation']} ({tops[0]['duration_ms']} ms)",
                t2=f"{tops[1]['operation']} ({tops[1]['duration_ms']} ms)",
                t3=f"{tops[2]['operation']} ({tops[2]['duration_ms']} ms)",
            )
        )

    lines.extend(["", "## Top 3 postes de lenteur (agrégé)", ""])
    if aggregate_totals:
        ranked = sorted(aggregate_totals.items(), key=lambda item: item[1], reverse=True)[:3]
        for index, (operation, duration_ms) in enumerate(ranked, start=1):
            lines.append(f"{index}. **{operation}** — {duration_ms} ms cumulés")
    else:
        lines.append("_Aucune donnée collectée — exécuter les benchmarks S1–S5 sur macOS._")

    lines.extend(
        [
            "",
            "## Analyse Apple Music (développeur)",
            "",
            "### Certain",
            "- Le workflow production utilise **AppleScript → Music.app** et **iTunes Search API publique**.",
            "- **MusicKit REST** nécessite un compte Apple Developer payant + JWT ; il n'est pas le chemin macOS par défaut.",
            "",
            "### Probable",
            "- La lenteur dominante vient de **N appels osascript** + pacing + clear playlist, indépendamment du compte développeur.",
            "",
            "### À vérifier (benchmark)",
            "- Part exacte : bridge cold start vs AppleScript vs iTunes HTTP vs cache IdentityCache.",
            "- Gain hypothétique MusicKit API vs AppleScript (nécessite tokens développeur).",
            "",
            "### Relève de",
            "| Domaine | Opérations mesurées |",
            "|---------|---------------------|",
            "| Music.app / AppleScript | `music_app.*`, `applescript.*`, `delivery.*` |",
            "| API Apple Music / MusicKit | `itunes.*`, `catalog.*` (expérimental hors scope baseline) |",
            "| Bridge Python | `bridge.*`, `context.*`, `generate.*` |",
            "",
            "## Prochaines étapes (5.3.2)",
            "",
            "1. Valider le top 3 sur 3 exécutions médianes par scénario.",
            "2. Appliquer un quick win à la fois avec mesure avant/après.",
            "",
        ]
    )
    return "\n".join(lines)


def write_baseline_markdown(
    runs: list[dict[str, Any]],
    reports_dir: Path,
    *,
    machine_label: str = "",
    notes: str = "",
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "phase-5-3-baseline.md"
    path.write_text(
        render_baseline_markdown(runs, machine_label=machine_label, notes=notes),
        encoding="utf-8",
    )
    return path
