from __future__ import annotations

from dataclasses import dataclass, field

from playlist_builder.observability.events import EventCategory, ResonanceEvent, ResonanceEventKind


@dataclass
class MetricsCollector:
    """Lightweight in-memory metrics — counters and duration totals by event kind."""

    event_counts: dict[str, int] = field(default_factory=dict)
    success_counts: dict[str, int] = field(default_factory=dict)
    failure_counts: dict[str, int] = field(default_factory=dict)
    duration_totals_ms: dict[str, int] = field(default_factory=dict)
    duration_samples: dict[str, int] = field(default_factory=dict)

    def record_event(self, event: ResonanceEvent) -> None:
        kind = event.kind.value
        self.event_counts[kind] = self.event_counts.get(kind, 0) + 1
        if event.success is True:
            self.success_counts[kind] = self.success_counts.get(kind, 0) + 1
        elif event.success is False:
            self.failure_counts[kind] = self.failure_counts.get(kind, 0) + 1
        if event.duration_ms is not None:
            self.duration_totals_ms[kind] = self.duration_totals_ms.get(kind, 0) + event.duration_ms
            self.duration_samples[kind] = self.duration_samples.get(kind, 0) + 1

    def counter(self, kind: ResonanceEventKind | str) -> int:
        key = kind.value if isinstance(kind, ResonanceEventKind) else kind
        return self.event_counts.get(key, 0)

    def average_duration_ms(self, kind: ResonanceEventKind | str) -> int | None:
        key = kind.value if isinstance(kind, ResonanceEventKind) else kind
        samples = self.duration_samples.get(key, 0)
        if samples == 0:
            return None
        return self.duration_totals_ms.get(key, 0) // samples

    def summary(self) -> dict[str, object]:
        return {
            "event_counts": dict(sorted(self.event_counts.items())),
            "success_counts": dict(sorted(self.success_counts.items())),
            "failure_counts": dict(sorted(self.failure_counts.items())),
            "average_duration_ms": {
                kind: self.average_duration_ms(kind)
                for kind in self.duration_samples
            },
        }

    def reset(self) -> None:
        self.event_counts.clear()
        self.success_counts.clear()
        self.failure_counts.clear()
        self.duration_totals_ms.clear()
        self.duration_samples.clear()
