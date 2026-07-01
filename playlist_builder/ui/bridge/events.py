from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from playlist_builder.ui.shared.validation import dto_to_dict


class BridgeEventType(StrEnum):
    """Streamable bridge events for long-running commands."""

    STARTED = "started"
    PROGRESS = "progress"
    DIAGNOSTIC = "diagnostic"
    COMPLETED = "completed"
    ERROR = "error"
    MANUAL_ACQUISITION_REQUIRED = "manual_acquisition_required"


@dataclass(frozen=True, slots=True)
class BridgeEvent:
    id: str
    event: BridgeEventType
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": "event",
            "event": self.event.value,
            "payload": self.payload,
        }


def started_event(request_id: str, *, command: str, message: str = "") -> BridgeEvent:
    payload: dict[str, Any] = {"command": command}
    if message:
        payload["message"] = message
    return BridgeEvent(id=request_id, event=BridgeEventType.STARTED, payload=payload)


def progress_event(request_id: str, **fields: Any) -> BridgeEvent:
    return BridgeEvent(id=request_id, event=BridgeEventType.PROGRESS, payload=dict(fields))


def diagnostic_event(request_id: str, **fields: Any) -> BridgeEvent:
    return BridgeEvent(id=request_id, event=BridgeEventType.DIAGNOSTIC, payload=dict(fields))


def completed_event(request_id: str, *, summary: dict[str, Any] | None = None) -> BridgeEvent:
    return BridgeEvent(
        id=request_id,
        event=BridgeEventType.COMPLETED,
        payload=summary or {},
    )


def manual_acquisition_required_event(
    request_id: str,
    *,
    token: str,
    artist: str,
    title: str,
    instructions: str,
    catalog_label: str = "",
    import_session_id: str = "",
) -> BridgeEvent:
    payload: dict[str, Any] = {
        "token": token,
        "artist": artist,
        "title": title,
        "instructions": instructions,
        "catalog_label": catalog_label,
    }
    if import_session_id:
        payload["import_session_id"] = import_session_id
    return BridgeEvent(
        id=request_id,
        event=BridgeEventType.MANUAL_ACQUISITION_REQUIRED,
        payload=payload,
    )


def error_event(request_id: str, *, code: str, message: str) -> BridgeEvent:
    return BridgeEvent(
        id=request_id,
        event=BridgeEventType.ERROR,
        payload={"code": code, "message": message},
    )


def serialize_event_data(data: Any) -> dict[str, Any]:
    if hasattr(data, "to_dict") and callable(data.to_dict):
        result = data.to_dict()
        return result if isinstance(result, dict) else {"value": result}
    return dto_to_dict(data) if hasattr(data, "__dataclass_fields__") else {"value": data}
