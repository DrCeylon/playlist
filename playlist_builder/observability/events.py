from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class EventCategory(StrEnum):
    """High-level observability domain — provider-agnostic."""

    SYNC = "sync"
    REPOSITORY = "repository"
    SNAPSHOT = "snapshot"
    PROVIDER = "provider"
    IMPORT = "import"
    GENERATION = "generation"
    SYSTEM = "system"


class ResonanceEventKind(StrEnum):
    """Strongly typed business event identifiers."""

    SYNC_PLAN_COMPLETED = "sync.plan.completed"
    SYNC_APPLY_STARTED = "sync.apply.started"
    SYNC_APPLY_COMPLETED = "sync.apply.completed"
    SYNC_APPLY_FAILED = "sync.apply.failed"
    SYNC_APPLY_BLOCKED = "sync.apply.blocked"
    REPOSITORY_UPSERT = "repository.playlist.upsert"
    SNAPSHOT_STORED = "snapshot.stored"
    PROVIDER_CALL = "provider.call"
    IMPORT_PHASE = "import.phase"
    GENERATION_COMPLETED = "generation.completed"
    HEALTH_CHECK = "system.health_check"


@dataclass(frozen=True, slots=True)
class ResonanceEvent:
    """Immutable business event for timelines, audit, and export."""

    kind: ResonanceEventKind
    category: EventCategory
    message: str
    timestamp_iso: str
    correlation_id: str = ""
    duration_ms: int | None = None
    success: bool | None = None
    local_playlist_id: str = ""
    provider_id: str = ""
    operation_id: str = ""
    attributes: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "kind": self.kind.value,
            "category": self.category.value,
            "message": self.message,
            "timestamp_iso": self.timestamp_iso,
            "correlation_id": self.correlation_id,
        }
        if self.duration_ms is not None:
            payload["duration_ms"] = self.duration_ms
        if self.success is not None:
            payload["success"] = self.success
        if self.local_playlist_id:
            payload["local_playlist_id"] = self.local_playlist_id
        if self.provider_id:
            payload["provider_id"] = self.provider_id
        if self.operation_id:
            payload["operation_id"] = self.operation_id
        if self.attributes:
            payload["attributes"] = {key: value for key, value in self.attributes}
        return payload

    @classmethod
    def now(
        cls,
        *,
        kind: ResonanceEventKind,
        category: EventCategory,
        message: str,
        correlation_id: str = "",
        **kwargs: Any,
    ) -> ResonanceEvent:
        cid = correlation_id or str(uuid4())
        attrs = kwargs.pop("attributes", ())
        return cls(
            kind=kind,
            category=category,
            message=message,
            timestamp_iso=datetime.now(UTC).isoformat(timespec="milliseconds"),
            correlation_id=cid,
            attributes=attrs if isinstance(attrs, tuple) else tuple(attrs),
            **kwargs,
        )
