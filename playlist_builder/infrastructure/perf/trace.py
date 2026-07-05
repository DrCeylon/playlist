from __future__ import annotations

import json
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

PERF_LOG_PREFIX = "resonance-perf:"
ENV_PERF_TRACE = "RESONANCE_PERF_TRACE"


def perf_trace_enabled() -> bool:
    value = os.environ.get(ENV_PERF_TRACE, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def perf_is_active() -> bool:
    return perf_trace_enabled() or _ACTIVE_SESSION is not None


@dataclass(frozen=True, slots=True)
class PerfSpan:
    phase: str
    operation: str
    duration_ms: int
    batch_index: int | None = None
    track_index: int | None = None
    cache_hit: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "phase": self.phase,
            "operation": self.operation,
            "duration_ms": self.duration_ms,
        }
        if self.batch_index is not None:
            payload["batch_index"] = self.batch_index
        if self.track_index is not None:
            payload["track_index"] = self.track_index
        if self.cache_hit is not None:
            payload["cache_hit"] = self.cache_hit
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


class PerfSession:
    """Collects perf spans for a single benchmark or import/generation run."""

    def __init__(
        self,
        *,
        scenario: str = "",
        operation: str = "",
        track_count: int | None = None,
        cache_mode: str = "",
    ) -> None:
        self.scenario = scenario
        self.operation = operation
        self.track_count = track_count
        self.cache_mode = cache_mode
        self.spans: list[PerfSpan] = []
        self.started_at = time.perf_counter()
        self._previous: PerfSession | None = None

    def __enter__(self) -> PerfSession:
        global _ACTIVE_SESSION
        self._previous = _ACTIVE_SESSION
        _ACTIVE_SESSION = self
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        global _ACTIVE_SESSION
        _ACTIVE_SESSION = self._previous

    def record(self, span: PerfSpan) -> None:
        self.spans.append(span)
        if perf_trace_enabled():
            _emit_stderr(span)

    @property
    def total_duration_ms(self) -> int:
        return int((time.perf_counter() - self.started_at) * 1000)

    def summary_by_operation(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        for span in self.spans:
            key = f"{span.phase}.{span.operation}"
            totals[key] = totals.get(key, 0) + span.duration_ms
        return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))

    def top_operations(self, limit: int = 3) -> list[tuple[str, int]]:
        return list(self.summary_by_operation().items())[:limit]

    def to_report_payload(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "operation": self.operation,
            "track_count": self.track_count,
            "cache_mode": self.cache_mode,
            "total_duration_ms": self.total_duration_ms,
            "span_count": len(self.spans),
            "spans": [span.to_dict() for span in self.spans],
            "summary_by_operation": self.summary_by_operation(),
            "top_operations": [
                {"operation": name, "duration_ms": duration_ms}
                for name, duration_ms in self.top_operations()
            ],
        }


_ACTIVE_SESSION: PerfSession | None = None


def current_perf_session() -> PerfSession | None:
    return _ACTIVE_SESSION


def perf_record(
    phase: str,
    operation: str,
    duration_ms: int,
    *,
    batch_index: int | None = None,
    track_index: int | None = None,
    cache_hit: bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    if not perf_is_active():
        return
    span = PerfSpan(
        phase=phase,
        operation=operation,
        duration_ms=max(0, duration_ms),
        batch_index=batch_index,
        track_index=track_index,
        cache_hit=cache_hit,
        metadata=dict(metadata or ()),
    )
    session = _ACTIVE_SESSION
    if session is not None:
        session.record(span)
    elif perf_trace_enabled():
        _emit_stderr(span)


@contextmanager
def perf_span(
    phase: str,
    operation: str,
    *,
    batch_index: int | None = None,
    track_index: int | None = None,
    cache_hit: bool | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[None]:
    if not perf_is_active():
        yield
        return
    started = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = int((time.perf_counter() - started) * 1000)
        perf_record(
            phase,
            operation,
            duration_ms,
            batch_index=batch_index,
            track_index=track_index,
            cache_hit=cache_hit,
            metadata=metadata,
        )


def _emit_stderr(span: PerfSpan) -> None:
    print(f"{PERF_LOG_PREFIX} {json.dumps(span.to_dict(), ensure_ascii=False)}", file=sys.stderr, flush=True)
