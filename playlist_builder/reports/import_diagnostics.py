from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from playlist_builder.canonical.models import CanonicalImportReport
from playlist_builder.core.models import TrackAddResult, TrackAddStatus


def write_import_diagnostics(
    playlist_name: str,
    report: CanonicalImportReport,
    aligned_results: list[TrackAddResult],
    reports_dir: Path,
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"import_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    payload = {
        "playlist_name": playlist_name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "added": sum(1 for result in aligned_results if result.status == TrackAddStatus.ADDED),
            "not_found": sum(1 for result in aligned_results if result.status == TrackAddStatus.NOT_FOUND),
            "skipped": sum(1 for result in aligned_results if result.status == TrackAddStatus.SKIPPED),
            "errors": sum(1 for result in aligned_results if result.status == TrackAddStatus.ERROR),
        },
        "tracks": [
            {
                "artist": item.track.artist.name,
                "title": item.track.title,
                "section": item.section_name,
                "status": item.status.value,
                "error": item.error,
            }
            for item in report.results
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
