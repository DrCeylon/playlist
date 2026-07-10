from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from playlist_builder.app.factory import AppContext
from playlist_builder.observability import build_health_report, get_default_bus
from playlist_builder.observability.events import EventCategory, ResonanceEvent, ResonanceEventKind
from playlist_builder.ui.shared.dto import DiagnosticEvent, ProviderOption
from playlist_builder.ui.shared.dto.enums import DiagnosticLevel


def build_diagnostics_snapshot(
    context: AppContext,
    *,
    providers: tuple[ProviderOption, ...],
    reports_dir: Path = Path("reports"),
    recent_report_limit: int = 5,
) -> tuple[dict[str, Any], tuple[DiagnosticEvent, ...]]:
    """Build a provider-neutral diagnostics snapshot for the Engine Bridge."""

    started = time.perf_counter()
    settings = context.settings
    provider_summaries = _provider_summaries(providers)
    catalog_entries = _count_cache_entries(settings.catalog_cache_path)
    identity_entries = _count_cache_entries(settings.identity_cache_path)
    recent_reports = _load_recent_reports(reports_dir, limit=recent_report_limit)
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    bus = get_default_bus()
    health = build_health_report(context, providers=providers, bus=bus)
    bus.emit(
        ResonanceEvent.now(
            kind=ResonanceEventKind.HEALTH_CHECK,
            category=EventCategory.SYSTEM,
            message=f"Diagnostics health: {health['status']}",
            success=health["status"] == "ok",
        )
    )

    summary: dict[str, Any] = {
        "bridge_status": "connected",
        "platform": sys.platform,
        "execution_ms": elapsed_ms,
        "catalog_cache_entries": catalog_entries,
        "identity_cache_entries": identity_entries,
        "catalog_cache_enabled": settings.use_catalog_cache,
        "country_code": settings.country_code,
        "active_providers": provider_summaries,
        "recent_reports": recent_reports,
        "reports_directory": str(reports_dir),
        "observability": {
            "api_version": health["api_version"],
            "health": health,
            "metrics": bus.metrics.summary(),
            "sync_timeline": list(bus.sync_timeline(limit=20)),
            "event_count": bus.event_count(),
        },
    }

    events = _events_from_snapshot(summary)
    return summary, events


def _provider_summaries(providers: tuple[ProviderOption, ...]) -> list[dict[str, Any]]:
    return [
        {
            "provider_id": provider.provider_id.value,
            "display_name": provider.display_name,
            "is_available": provider.is_available,
            "is_connected": provider.is_connected,
            "unavailable_reason": provider.unavailable_reason,
        }
        for provider in providers
    ]


def _count_cache_entries(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    return len(data) if isinstance(data, dict) else 0


def _load_recent_reports(reports_dir: Path, *, limit: int) -> list[dict[str, Any]]:
    if not reports_dir.exists():
        return []

    summaries: list[dict[str, Any]] = []
    for path in sorted(reports_dir.glob("import_diagnostics_*.json"), reverse=True)[:limit]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue

        summary = {
            "filename": path.name,
            "playlist_name": str(payload.get("playlist_name", "")),
            "generated_at": str(payload.get("generated_at", "")),
            "track_summary": payload.get("summary", {}),
        }
        encoded = json.dumps(summary, ensure_ascii=False)
        if "persistent_id" in encoded:
            continue
        summaries.append(summary)
    return summaries


def _events_from_snapshot(summary: dict[str, Any]) -> tuple[DiagnosticEvent, ...]:
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    events: list[DiagnosticEvent] = [
        DiagnosticEvent(
            phase="bridge",
            message="Engine Bridge connecté",
            level=DiagnosticLevel.INFO,
            timestamp_iso=timestamp,
            payload=(
                ("bridge_status", str(summary.get("bridge_status", ""))),
                ("platform", str(summary.get("platform", ""))),
                ("execution_ms", str(summary.get("execution_ms", 0))),
            ),
        ),
        DiagnosticEvent(
            phase="cache",
            message="Statistiques de cache",
            level=DiagnosticLevel.INFO,
            timestamp_iso=timestamp,
            payload=(
                ("catalog_cache_entries", str(summary.get("catalog_cache_entries", 0))),
                ("identity_cache_entries", str(summary.get("identity_cache_entries", 0))),
            ),
        ),
    ]

    for provider in summary.get("active_providers", []):
        if not isinstance(provider, dict):
            continue
        level = DiagnosticLevel.INFO if provider.get("is_available") else DiagnosticLevel.WARNING
        events.append(
            DiagnosticEvent(
                phase="provider",
                message=f"Provider {provider.get('display_name', '')}",
                level=level,
                timestamp_iso=timestamp,
                payload=(
                    ("provider_id", str(provider.get("provider_id", ""))),
                    ("is_available", str(provider.get("is_available", False))),
                    ("is_connected", str(provider.get("is_connected", False))),
                ),
            )
        )

    for report in summary.get("recent_reports", []):
        if not isinstance(report, dict):
            continue
        track_summary = report.get("track_summary", {})
        if not isinstance(track_summary, dict):
            track_summary = {}
        events.append(
            DiagnosticEvent(
                phase="import_report",
                message=f"Rapport {report.get('playlist_name', '')}",
                level=DiagnosticLevel.INFO,
                timestamp_iso=str(report.get("generated_at", timestamp)),
                payload=(
                    ("filename", str(report.get("filename", ""))),
                    ("added", str(track_summary.get("added", 0))),
                    ("not_found", str(track_summary.get("not_found", 0))),
                    ("errors", str(track_summary.get("errors", 0))),
                ),
            )
        )

    return tuple(events)
