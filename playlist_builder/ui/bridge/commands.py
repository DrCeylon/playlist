from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.bridge.errors import InvalidBridgeRequestError
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
from playlist_builder.ui.shared.dto.autocomplete import (
    AutocompleteContext,
    AutocompleteEntityKind,
    AutocompleteRequest,
    AutocompleteResponse,
)
from playlist_builder.ui.shared.dto.enums import DiagnosticLevel
from playlist_builder.ui.shared.validation import ValidationError, dto_to_dict


class BridgeCommand(StrEnum):
    LIST_PROVIDERS = "list_providers"
    VALIDATE_GENERATION_REQUEST = "validate_generation_request"
    GENERATE_PLAYLIST = "generate_playlist"
    IMPORT_PLAYLIST = "import_playlist"
    DIAGNOSTICS = "diagnostics"
    CONTINUE_MANUAL_ACQUISITION = "continue_manual_acquisition"
    LIST_HISTORY = "list_history"
    GET_HISTORY_SESSION = "get_history_session"
    DELETE_HISTORY_SESSION = "delete_history_session"
    CLEAR_HISTORY = "clear_history"
    REPLAY_GENERATION = "replay_generation"
    EXPORT_HISTORY_SESSION = "export_history_session"
    AUTOCOMPLETE_SEARCH = "autocomplete_search"


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
    history_session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"generation": dto_to_dict(self.result)}
        if self.history_session_id:
            payload["history_session_id"] = self.history_session_id
        return payload


@dataclass(frozen=True, slots=True)
class ImportPlaylistResult:
    import_result: ImportResultState
    history_session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"import": dto_to_dict(self.import_result)}
        if self.history_session_id:
            payload["history_session_id"] = self.history_session_id
        return payload


@dataclass(frozen=True, slots=True)
class DiagnosticsResult:
    engine_version: str
    summary: dict[str, Any] = field(default_factory=dict)
    events: tuple[DiagnosticEvent, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "engine_version": self.engine_version,
            "events": [dto_to_dict(event) for event in self.events],
        }
        if self.summary:
            payload["summary"] = self.summary
        return payload


@dataclass(frozen=True, slots=True)
class HistoryListResult:
    sessions: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"sessions": [dict(item) for item in self.sessions]}


@dataclass(frozen=True, slots=True)
class HistorySessionResult:
    session: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"session": dict(self.session) if self.session else None}


@dataclass(frozen=True, slots=True)
class AutocompleteSearchResult:
    response: AutocompleteResponse

    def to_dict(self) -> dict[str, Any]:
        return self.response.to_dict()


def autocomplete_request_from_dict(data: dict[str, Any]) -> AutocompleteRequest:
    provider_id = _parse_provider_id(data.get("provider_id", ProviderId.APPLE_MUSIC.value))
    entity_raw = str(data.get("entity_kind", "")).strip()
    try:
        entity_kind = AutocompleteEntityKind(entity_raw)
    except ValueError as exc:
        raise InvalidBridgeRequestError(f"entity_kind invalide : {entity_raw!r}") from exc

    query = str(data.get("query", ""))
    limit = _optional_int(data.get("limit", 10), field_name="limit") or 10
    if limit < 1:
        raise InvalidBridgeRequestError("limit doit être >= 1.")

    context_data = data.get("context", {})
    context: AutocompleteContext | None = None
    if isinstance(context_data, dict) and context_data:
        context = AutocompleteContext(
            artist_name=str(context_data.get("artist_name", "")),
            artist_id=str(context_data.get("artist_id", "")),
        )

    return AutocompleteRequest(
        provider_id=provider_id,
        entity_kind=entity_kind,
        query=query,
        limit=limit,
        context=context,
    )


def parse_bridge_request(payload: dict[str, Any]) -> BridgeRequest:
    if not isinstance(payload, dict):
        raise InvalidBridgeRequestError("Bridge request must be an object.")

    request_id = str(payload.get("id", "")).strip()
    if not request_id:
        raise InvalidBridgeRequestError("Bridge request id is required.")

    command_raw = payload.get("command")
    if not isinstance(command_raw, str):
        raise InvalidBridgeRequestError("Bridge command must be a string.")

    try:
        command = BridgeCommand(command_raw.strip())
    except ValueError as exc:
        raise InvalidBridgeRequestError(f"Unknown bridge command: {command_raw!r}") from exc

    params = payload.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise InvalidBridgeRequestError("Bridge params must be an object.")

    return BridgeRequest(id=request_id, command=command, params=params)


def playlist_generation_request_from_dict(data: dict[str, Any]) -> PlaylistGenerationRequest:
    if not isinstance(data, dict):
        raise InvalidBridgeRequestError("Generation request must be an object.")

    provider_id = _parse_provider_id(data.get("provider_id", ProviderId.APPLE_MUSIC.value))
    seeds = tuple(_seed_from_dict(item) for item in _parse_object_list(data.get("seeds", ()), field_name="seeds"))
    keywords = tuple(str(item).strip() for item in _as_list(data.get("keywords", ())) if str(item).strip())
    exclusions = tuple(
        _exclusion_from_dict(item) for item in _parse_object_list(data.get("exclusions", ()), field_name="exclusions")
    )
    energy_curve = _energy_curve_from_dict(data.get("energy_curve", {}))

    return PlaylistGenerationRequest(
        name=str(data.get("name", "")),
        provider_id=provider_id,
        seeds=seeds,
        keywords=keywords,
        description=str(data.get("description", "")),
        target_track_count=_optional_int(data.get("target_track_count"), field_name="target_track_count"),
        target_duration_minutes=_optional_int(
            data.get("target_duration_minutes"),
            field_name="target_duration_minutes",
        ),
        energy_curve=energy_curve,
        exclusions=exclusions,
        playlist_theme=str(data.get("playlist_theme", "")),
    )


def _parse_provider_id(value: Any) -> ProviderId:
    try:
        return ProviderId(str(value))
    except ValueError as exc:
        raise InvalidBridgeRequestError(f"provider_id invalide : {value!r}") from exc


def _seed_from_dict(data: Any) -> SeedReference:
    if not isinstance(data, dict):
        raise InvalidBridgeRequestError("Chaque seed doit être un objet.")
    try:
        weight = float(data.get("weight", 1.0))
    except (TypeError, ValueError) as exc:
        raise InvalidBridgeRequestError("seed.weight invalide.") from exc
    return SeedReference(
        artist=str(data.get("artist", "")),
        title=str(data.get("title", "")),
        weight=weight,
    )


def _exclusion_from_dict(data: Any) -> ExclusionRule:
    if not isinstance(data, dict):
        raise InvalidBridgeRequestError("Chaque exclusion doit être un objet.")
    kind_raw = data.get("kind", "")
    try:
        kind = ExclusionKind(str(kind_raw))
    except ValueError as exc:
        raise InvalidBridgeRequestError(f"exclusion.kind invalide : {kind_raw!r}") from exc
    return ExclusionRule(
        kind=kind,
        value=str(data.get("value", "")),
        reason=str(data.get("reason", "")),
    )


def _energy_curve_from_dict(value: Any) -> EnergyCurveOption:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise InvalidBridgeRequestError("energy_curve doit être un objet.")
    profile_raw = value.get("profile", EnergyCurveProfile.RISING.value)
    try:
        profile = EnergyCurveProfile(str(profile_raw))
    except ValueError as exc:
        raise InvalidBridgeRequestError(f"energy_curve.profile invalide : {profile_raw!r}") from exc
    chapters = tuple(str(item).strip() for item in _as_list(value.get("chapter_labels", ())) if str(item).strip())
    return EnergyCurveOption(profile=profile, chapter_labels=chapters)


def diagnostic_event_from_dict(data: dict[str, Any]) -> DiagnosticEvent:
    if not isinstance(data, dict):
        raise InvalidBridgeRequestError("Diagnostic event must be an object.")
    level_raw = data.get("level", DiagnosticLevel.INFO.value)
    try:
        level = DiagnosticLevel(str(level_raw))
    except ValueError as exc:
        raise InvalidBridgeRequestError(f"diagnostic.level invalide : {level_raw!r}") from exc
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
        level=level,
        timestamp_iso=str(data.get("timestamp_iso", "")),
        payload=payload,
    )


def _parse_object_list(value: Any, *, field_name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise InvalidBridgeRequestError(f"{field_name} doit être une liste.")
    return list(value)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _optional_int(value: Any, *, field_name: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise InvalidBridgeRequestError(f"{field_name} invalide : {value!r}") from exc
