from __future__ import annotations

from datetime import datetime
from pathlib import Path

from playlist_builder.core.models import TrackAddResult, TrackAddStatus


def write_playlist_report(
    playlist_name: str,
    results: list[TrackAddResult],
    reports_dir: Path,
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    not_found = [r.track for r in results if r.status == TrackAddStatus.NOT_FOUND]
    skipped = [r.track for r in results if r.status == TrackAddStatus.SKIPPED]
    errors = [r for r in results if r.status == TrackAddStatus.ERROR]
    added = [r.track for r in results if r.status == TrackAddStatus.ADDED]

    lines = [
        f"Playlist: {playlist_name}",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"Added: {len(added)}",
        f"Not found: {len(not_found)}",
        f"Skipped: {len(skipped)}",
        f"Errors: {len(errors)}",
        "",
        "Not found:",
    ]
    lines += [f"- [{track.section}] {track.artist} - {track.title}" for track in not_found]
    lines += ["", "Already present / skipped:"]
    lines += [f"- [{track.section}] {track.artist} - {track.title}" for track in skipped]
    if errors:
        lines += ["", "Errors:"]
        lines += [
            f"- [{result.track.section}] {result.track.artist} - {result.track.title}: {result.error}"
            for result in errors
        ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
