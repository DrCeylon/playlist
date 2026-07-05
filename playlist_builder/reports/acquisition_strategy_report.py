from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playlist_builder.integration.apple_music.acquisition_experiments import (
    AcquisitionExperimentInput,
    AcquisitionStrategyResult,
)


def write_acquisition_strategy_reports(
    *,
    experiment_input: AcquisitionExperimentInput,
    results: list[AcquisitionStrategyResult],
    summary: dict[str, Any],
    reports_dir: Path,
    machine_label: str = "",
    notes: str = "",
) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = reports_dir / f"acquisition_strategy_{timestamp}.json"
    md_path = reports_dir / f"acquisition_strategy_{timestamp}.md"

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "5.3.3",
        "machine_label": machine_label,
        "notes": notes,
        "input": {
            "url": experiment_input.url,
            "track_id": experiment_input.track_id,
            "artist": experiment_input.artist,
            "title": experiment_input.title,
            "search_terms": list(experiment_input.search_terms),
            "activate_music": experiment_input.activate_music,
        },
        "summary": summary,
        "results": [result.to_dict() for result in results],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(
        render_acquisition_strategy_markdown(payload),
        encoding="utf-8",
    )
    return json_path, md_path


def render_acquisition_strategy_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 5.3.3 — Rapport expérimental acquisition Apple Music",
        "",
        f"*Généré le {payload.get('generated_at', '')}*",
        "",
    ]
    machine = payload.get("machine_label", "")
    if machine:
        lines.extend([f"**Machine** : {machine}", ""])

    input_data = payload.get("input", {})
    lines.extend(
        [
            "## Morceau testé",
            "",
            f"- **URL** : {input_data.get('url', '—')}",
            f"- **Track ID** : {input_data.get('track_id', '—')}",
            f"- **Artiste** : {input_data.get('artist', '—')}",
            f"- **Titre** : {input_data.get('title', '—')}",
            "",
            "## Résumé",
            "",
        ]
    )
    summary = payload.get("summary", {})
    lines.append(f"- Stratégies exécutées : **{summary.get('strategy_count', 0)}**")
    lines.append(f"- Succès : **{summary.get('success_count', 0)}**")
    fastest = summary.get("fastest_success")
    if fastest:
        lines.append(
            f"- Plus rapide en succès : **{fastest.get('strategy_name')}** "
            f"({fastest.get('duration_ms')} ms, PID `{fastest.get('persistent_id', '')}`)"
        )
    else:
        lines.append("- Plus rapide en succès : _aucune stratégie automatique n'a réussi_")

    lines.extend(["", "## Résultats détaillés", "", "| Stratégie | Succès | Durée (ms) | PID | Biblio | Music activé | Erreur |", "|-----------|--------|------------|-----|--------|--------------|--------|"])
    for result in payload.get("results", []):
        error = (result.get("applescript_error") or "—").replace("|", "\\|")
        if len(error) > 80:
            error = error[:77] + "..."
        lines.append(
            "| {name} | {success} | {duration} | {pid} | {found} | {activated} | {error} |".format(
                name=result.get("strategy_name", "—"),
                success="✅" if result.get("success") else "❌",
                duration=result.get("duration_ms", "—"),
                pid=result.get("persistent_id") or "—",
                found="oui" if result.get("found_in_library") else "non",
                activated="oui" if result.get("music_app_activated") else "non",
                error=error or "—",
            )
        )

    notes = payload.get("notes", "")
    if notes:
        lines.extend(["", "## Notes", "", notes])

    lines.extend(
        [
            "",
            "## Critères de décision (rappel)",
            "",
            "1. La stratégie doit retourner un `persistent_id` bibliothèque utilisable par la livraison.",
            "2. La durée doit être mesurée et reproductible sur 3 runs.",
            "3. Aucune stratégie ne doit casser le workflow manuel existant.",
            "4. MusicKit reste hors scope tant que les stratégies AppleScript ne sont pas épuisées.",
            "",
        ]
    )
    return "\n".join(lines)
