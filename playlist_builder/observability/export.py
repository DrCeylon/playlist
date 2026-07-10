from __future__ import annotations

from typing import Any

from playlist_builder.observability.api_version import OBSERVABILITY_API_VERSION
from playlist_builder.observability.bus import ObservabilityBus, get_default_bus


def export_observability_bundle(
    bus: ObservabilityBus | None = None,
    *,
    health: dict[str, Any] | None = None,
    sync_operations: list[dict[str, Any]] | None = None,
    event_limit: int = 200,
) -> dict[str, Any]:
    """Export typed events, metrics, timeline, and health for UI / API / tests."""
    observability_bus = bus or get_default_bus()
    sync_ops = sync_operations or []
    return {
        "api_version": OBSERVABILITY_API_VERSION,
        "health": health or {"status": "unknown"},
        "metrics": observability_bus.metrics.summary(),
        "recent_events": [event.to_dict() for event in observability_bus.recent_events(limit=event_limit)],
        "sync_timeline": list(observability_bus.sync_timeline(limit=event_limit)),
        "sync_operations": sync_ops[:event_limit],
        "event_count": observability_bus.event_count(),
    }
