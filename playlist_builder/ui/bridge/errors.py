from __future__ import annotations

from enum import StrEnum


class BridgeErrorCode(StrEnum):
    """Stable error codes returned to SwiftUI / CLI bridge clients."""

    UNKNOWN_COMMAND = "unknown_command"
    INVALID_REQUEST = "invalid_request"
    VALIDATION_FAILED = "validation_failed"
    NOT_CONFIGURED = "not_configured"
    ENGINE_ERROR = "engine_error"


class BridgeError(Exception):
    """Controlled bridge failure with a machine-readable code."""

    def __init__(
        self,
        code: BridgeErrorCode,
        message: str,
        *,
        details: tuple[tuple[str, str], ...] = (),
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.details:
            payload["details"] = {key: value for key, value in self.details}
        return payload


class InvalidBridgeRequestError(BridgeError):
    """Raised when request JSON shape or field types/values are invalid."""

    def __init__(
        self,
        message: str,
        *,
        details: tuple[tuple[str, str], ...] = (),
    ) -> None:
        super().__init__(BridgeErrorCode.INVALID_REQUEST, message, details=details)
