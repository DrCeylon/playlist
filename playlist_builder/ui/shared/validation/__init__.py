from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationError:
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    errors: tuple[ValidationError, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def raise_if_invalid(self) -> None:
        if not self.is_valid:
            joined = "; ".join(f"{error.field}: {error.message}" for error in self.errors)
            raise ValueError(joined)


def merge_results(*results: ValidationResult) -> ValidationResult:
    errors: list[ValidationError] = []
    for result in results:
        errors.extend(result.errors)
    return ValidationResult(errors=tuple(errors))


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return dto_to_dict(value)
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    if isinstance(value, frozenset):
        return sorted(_serialize_value(item) for item in value)
    if isinstance(value, set):
        return sorted(_serialize_value(item) for item in value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    return value


def dto_to_dict(dto: Any) -> dict[str, Any]:
    if not is_dataclass(dto):
        raise TypeError(f"Expected dataclass, got {type(dto)!r}")
    return {field.name: _serialize_value(getattr(dto, field.name)) for field in fields(dto)}
