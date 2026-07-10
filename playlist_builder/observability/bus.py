from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from playlist_builder.observability.events import EventCategory, ResonanceEvent, ResonanceEventKind
from playlist_builder.observability.metrics import MetricsCollector


@dataclass
class ObservabilityBus:
    """In-process event bus with bounded retention. Complements stderr logs — does not replace them."""

    max_events: int = 2000
    _events: deque[ResonanceEvent] = field(default_factory=deque, init=False, repr=False)
    _metrics: MetricsCollector = field(default_factory=MetricsCollector, init=False, repr=False)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        self._events = deque(maxlen=self.max_events)

    def emit(self, event: ResonanceEvent) -> None:
        with self._lock:
            self._events.append(event)
            self._metrics.record_event(event)

    @property
    def metrics(self) -> MetricsCollector:
        return self._metrics

    def recent_events(
        self,
        *,
        limit: int = 100,
        category: EventCategory | None = None,
        local_playlist_id: str | None = None,
    ) -> tuple[ResonanceEvent, ...]:
        with self._lock:
            items = list(self._events)
        if category is not None:
            items = [event for event in items if event.category == category]
        if local_playlist_id:
            items = [event for event in items if event.local_playlist_id == local_playlist_id]
        return tuple(items[-limit:])

    def sync_timeline(self, *, local_playlist_id: str | None = None, limit: int = 50) -> tuple[dict[str, Any], ...]:
        events = self.recent_events(
            limit=limit,
            category=EventCategory.SYNC,
            local_playlist_id=local_playlist_id,
        )
        return tuple(event.to_dict() for event in events)

    def event_count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._metrics.reset()


_DEFAULT_BUS: ObservabilityBus | None = None


def get_default_bus() -> ObservabilityBus:
    global _DEFAULT_BUS
    if _DEFAULT_BUS is None:
        _DEFAULT_BUS = ObservabilityBus()
    return _DEFAULT_BUS


def reset_default_bus() -> None:
    """Test helper — replace the process-wide bus."""
    global _DEFAULT_BUS
    _DEFAULT_BUS = ObservabilityBus()
