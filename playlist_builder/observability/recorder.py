from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from playlist_builder.observability.bus import ObservabilityBus, get_default_bus
from playlist_builder.observability.events import EventCategory, ResonanceEvent, ResonanceEventKind


class NoOpObservabilityRecorder:
    """Disable observability emission (tests or hot paths)."""

    def record_sync_plan_completed(self, **kwargs: Any) -> str:
        return ""

    def record_sync_apply_started(self, **kwargs: Any) -> str:
        return ""

    def record_sync_apply_completed(self, **kwargs: Any) -> None:
        return None

    def record_sync_apply_failed(self, **kwargs: Any) -> None:
        return None

    def record_sync_apply_blocked(self, **kwargs: Any) -> None:
        return None


class ObservabilityRecorder:
    """Emits strongly typed sync/repository events to the bus."""

    def __init__(self, bus: ObservabilityBus | None = None) -> None:
        self._bus = bus or get_default_bus()

    @property
    def bus(self) -> ObservabilityBus:
        return self._bus

    def record_sync_plan_completed(
        self,
        *,
        local_playlist_id: str,
        provider_id: str,
        duration_ms: int,
        actions_total: int,
        conflicts_total: int,
        correlation_id: str = "",
    ) -> str:
        cid = correlation_id or str(uuid4())
        self._bus.emit(
            ResonanceEvent.now(
                kind=ResonanceEventKind.SYNC_PLAN_COMPLETED,
                category=EventCategory.SYNC,
                message="Sync plan computed",
                correlation_id=cid,
                duration_ms=duration_ms,
                success=True,
                local_playlist_id=local_playlist_id,
                provider_id=provider_id,
                attributes=(
                    ("actions_total", str(actions_total)),
                    ("conflicts_total", str(conflicts_total)),
                ),
            )
        )
        return cid

    def record_sync_apply_started(
        self,
        *,
        local_playlist_id: str,
        provider_id: str,
        operation_id: str,
        correlation_id: str = "",
    ) -> str:
        cid = correlation_id or str(uuid4())
        self._bus.emit(
            ResonanceEvent.now(
                kind=ResonanceEventKind.SYNC_APPLY_STARTED,
                category=EventCategory.SYNC,
                message="Sync apply started",
                correlation_id=cid,
                local_playlist_id=local_playlist_id,
                provider_id=provider_id,
                operation_id=operation_id,
            )
        )
        return cid

    def record_sync_apply_completed(
        self,
        *,
        local_playlist_id: str,
        provider_id: str,
        operation_id: str,
        duration_ms: int,
        status: str,
        actions_completed: int,
        actions_failed: int,
        correlation_id: str,
    ) -> None:
        self._bus.emit(
            ResonanceEvent.now(
                kind=ResonanceEventKind.SYNC_APPLY_COMPLETED,
                category=EventCategory.SYNC,
                message=f"Sync apply finished: {status}",
                correlation_id=correlation_id,
                duration_ms=duration_ms,
                success=actions_failed == 0,
                local_playlist_id=local_playlist_id,
                provider_id=provider_id,
                operation_id=operation_id,
                attributes=(
                    ("status", status),
                    ("actions_completed", str(actions_completed)),
                    ("actions_failed", str(actions_failed)),
                ),
            )
        )

    def record_sync_apply_failed(
        self,
        *,
        local_playlist_id: str,
        provider_id: str,
        operation_id: str,
        duration_ms: int,
        error_message: str,
        correlation_id: str,
    ) -> None:
        self._bus.emit(
            ResonanceEvent.now(
                kind=ResonanceEventKind.SYNC_APPLY_FAILED,
                category=EventCategory.SYNC,
                message=error_message,
                correlation_id=correlation_id,
                duration_ms=duration_ms,
                success=False,
                local_playlist_id=local_playlist_id,
                provider_id=provider_id,
                operation_id=operation_id,
            )
        )

    def record_sync_apply_blocked(
        self,
        *,
        local_playlist_id: str,
        provider_id: str,
        operation_id: str,
        reason: str,
        correlation_id: str = "",
    ) -> str:
        cid = correlation_id or str(uuid4())
        self._bus.emit(
            ResonanceEvent.now(
                kind=ResonanceEventKind.SYNC_APPLY_BLOCKED,
                category=EventCategory.SYNC,
                message=reason,
                correlation_id=cid,
                success=False,
                local_playlist_id=local_playlist_id,
                provider_id=provider_id,
                operation_id=operation_id,
                attributes=(("reason", reason),),
            )
        )
        return cid


class SyncApplyObservation:
    """Context manager for sync apply timing."""

    def __init__(self, recorder: ObservabilityRecorder, **context: str) -> None:
        self._recorder = recorder
        self._context = context
        self._started = 0.0
        self.correlation_id = ""

    def __enter__(self) -> SyncApplyObservation:
        self._started = time.perf_counter()
        self.correlation_id = self._recorder.record_sync_apply_started(**self._context)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        duration_ms = int((time.perf_counter() - self._started) * 1000)
        if exc is not None:
            self._recorder.record_sync_apply_failed(
                duration_ms=duration_ms,
                error_message=str(exc),
                correlation_id=self.correlation_id,
                **self._context,
            )
