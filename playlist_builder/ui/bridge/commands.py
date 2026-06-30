from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto import (
    DiagnosticEvent,
    EnergyCurveOption,
    EnergyCurveProfile,
    ExclusionKind,
    ExclusionRule,
    ImportResultState,
    PlaylistGenerationRequest,
    PlaylistGenerationResult,
    ProviderOption,
    SeedReference,
)
from playlist_builder.ui.shared.dto.enums import DiagnosticLevel
from playlist_builder.ui.shared.validation import ValidationError, dto_to_dict


class BridgeCommand(StrEnum):
    LIST_PROVIDERS = "list_providers"
    VALIDATE_GENERATION_REQUEST = "validate_generation_request"
    GENERATE_PLAYLIST = "generate_playlist"
    IMPORT_PLAYLIST = "import_playlist"
    DIAGNOSTICS = "diagnostics"


@dataclass(frozen=True, slots=True)
class BridgeRequest:
    id: str
    command: BridgeCommand
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BridgeResponse:
    id: str
    ok: bool
    result: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"id": self.id, "type": "response", "ok": self.ok}
        if self.ok:
            payload["result"] = self.result
        else:
            payload["error"] = self.error or {}
        return payload


@dataclass(frozen=True, slots=True)
class ListProvidersResult:
    providers: tuple[ProviderOption, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"providers": [dto_to_dict(provider) for provider in self.providers]}


@dataclass(frozen=True, slots=True)
class ValidateGenerationRequestResult:
    valid: bool
    errors: tuple[ValidationError, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [{"field": error.field, "message": error.message} for error in self.errors],
        }


@dataclass(frozen=True, slots=True)
class GeneratePlaylistResult:
    result: PlaylistGenerationResult

    def to_dict(self) -> dict[str, Any]:
        return {"generation": dto_to_dict(self.result)}


@dataclass(frozen=True, slots=True)
class ImportPlaylistResult:
    import_result: ImportResultState

    def to_dict(self) -> dict[str, Any]:
        return {"import": dto_to_dict(self.import_result)}


@dataclass(frozen=True, slots=True)
class DiagnosticsResult:
    engine_version: str
    events: tuple[DiagnosticEvent, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "events": [dto_to_dict(event) for event in self.events],
        }


def parse_bridge_request(payload: dict[str, Any]) -> BridgeRequest:
    request_id = str(payload.get("id", "")).strip()
    if not request_id:
        raise ValueError("Bridge request id is required.")

    command_raw = payload.get("command")
    if not isinstance(command_raw, str):
        raise ValueError("Bridge command must be a string.")

    try:
        command = BridgeCommand(command_raw.strip())
    except ValueError as exc:
        raise ValueError(f"Unknown bridge command: {command_raw!r}") from exc

    params = payload.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ValueError("Bridge params must be an object.")

    return BridgeRequest(id=request_id, command=command, params=params)


def playlist_generation_request_from_dict(data: dict[str, Any]) -> PlaylistGenerationRequest:
    if not isinstance(data, dict):
        raise ValueError("Generation request must be an object.")

    provider_raw = data.get("provider_id", ProviderId.APPLE_MUSIC.value)
    provider_id = ProviderId(str(provider_raw))

    seeds = tuple(_seed_from_dict(item) for item in _as_list(data.get("seeds", ())))
    keywords = tuple(str(item).strip() for item in _as_list(data.get("keywords", ())) if str(item).strip())
    exclusions = tuple(_exclusion_from_dict(item) for item in _as_list(data.get("exclusions", ())))

    energy_raw = data.get("energy_curve", {})
    energy_curve = _energy_curve_from_dict(energy_raw if isinstance(energy_raw, dict) else {})

    return PlaylistGenerationRequest(
        name=str(data.get("name", "")),
        provider_id=provider_id,
        seeds=seeds,
        keywords=keywords,
        description=str(data.get("description", "")),
        target_track_count=_optional_int(data.get("target_track_count")),
        target_duration_minutes=_optional_int(data.get("target_duration_minutes")),
        energy_curve=energy_curve,
        exclusions=exclusions,
        playlist_theme=str(data.get("playlist_theme", "")),
    )


def _seed_from_dict(data: Any) -> SeedReference:
    if not isinstance(data, dict):
        raise ValueError("Seed must be an object.")
    weight = float(data.get("weight", 1.0))
    return SeedReference(
        artist=str(data.get("artist", "")),
        title=str(data.get("title", "")),
        weight=weight,
    )


def _exclusion_from_dict(data: Any) -> ExclusionRule:
    if not isinstance(data, dict):
        raise ValueError("Exclusion must be an object.")
    kind = ExclusionKind(str(data.get("kind", "")))
    return ExclusionRule(
        kind=kind,
        value=str(data.get("value", "")),
        reason=str(data.get("reason", "")),
    )


def _energy_curve_from_dict(data: dict[str, Any]) -> EnergyCurveOption:
    profile_raw = data.get("profile", EnergyCurveProfile.RISING.value)
    profile = EnergyCurveProfile(str(profile_raw))
    chapters = tuple(str(item).strip() for item in _as_list(data.get("chapter_labels", ())) if str(item).strip())
    return EnergyCurveOption(profile=profile, chapter_labels=chapters)


def diagnostic_event_from_dict(data: dict[str, Any]) -> DiagnosticEvent:
    level_raw = data.get("level", DiagnosticLevel.INFO.value)
    payload_raw = data.get("payload", ())
    payload: tuple[tuple[str, str], ...] = ()
    if isinstance(payload_raw, list):
        pairs: list[tuple[str, str]] = []
        for item in payload_raw:
            if isinstance(item, dict) and "key" in item and "value" in item:
                pairs.append((str(item["key"]), str(item["value"])))
        payload = tuple(pairs)
    return DiagnosticEvent(
        phase=str(data.get("phase", "")),
        message=str(data.get("message", "")),
        level=DiagnosticLevel(str(level_raw)),
        timestamp_iso=str(data.get("timestamp_iso", "")),
        payload=payload,
    )


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)
