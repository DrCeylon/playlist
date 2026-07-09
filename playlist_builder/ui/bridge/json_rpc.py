from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from playlist_builder import __version__
from playlist_builder.core.models import PlaylistDefinition, PlaylistSection, TrackAddResult, TrackAddStatus, TrackRef
from playlist_builder.ui.bridge.commands import (
    BridgeCommand,
    BridgeRequest,
    BridgeResponse,
    DiagnosticsResult,
    GeneratePlaylistResult,
    ImportPlaylistResult,
    ListProvidersResult,
    ValidateGenerationRequestResult,
    AutocompleteSearchResult,
    autocomplete_request_from_dict,
    parse_bridge_request,
    playlist_generation_request_from_dict,
)
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode, InvalidBridgeRequestError
from playlist_builder.ui.bridge.events import BridgeEvent, completed_event, started_event
from playlist_builder.ui.bridge.protocol import EngineBridge, EngineBridgeBackend
from playlist_builder.infrastructure.manual_continue_trace import begin_session, log as manual_continue_trace
from playlist_builder.ui.shared.dto import ImportResultState, ProviderOption, default_provider_options
from playlist_builder.ui.shared.validation.generation import validate_playlist_generation_request


@dataclass(slots=True)
class JsonRpcEngineBridge(EngineBridge):
    """JSON-lines engine bridge for future SwiftUI and automation clients."""

    backend: EngineBridgeBackend | None = None

    def handle(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        return list(self.handle_messages(request))

    def handle_messages(self, request: dict[str, Any]) -> Iterator[dict[str, Any]]:
        try:
            bridge_request = parse_bridge_request(request)
        except InvalidBridgeRequestError as exc:
            yield _error_response(str(request.get("id", "")), exc.code, exc.message, details=exc.details).to_dict()
            return
        except ValueError as exc:
            yield _error_response(str(request.get("id", "")), BridgeErrorCode.INVALID_REQUEST, str(exc)).to_dict()
            return

        try:
            yield from self._dispatch(bridge_request)
        except InvalidBridgeRequestError as exc:
            yield _error_response(bridge_request.id, exc.code, exc.message, details=exc.details).to_dict()
        except BridgeError as exc:
            yield _error_response(bridge_request.id, exc.code, exc.message, details=exc.details).to_dict()
        except Exception as exc:
            yield _error_response(
                bridge_request.id,
                BridgeErrorCode.ENGINE_ERROR,
                str(exc),
            ).to_dict()

    def _dispatch(self, request: BridgeRequest) -> Iterator[dict[str, Any]]:
        if request.command == BridgeCommand.LIST_PROVIDERS:
            result = self._list_providers()
            yield BridgeResponse(id=request.id, ok=True, result=result.to_dict()).to_dict()
            return

        if request.command == BridgeCommand.VALIDATE_GENERATION_REQUEST:
            result = self._validate_generation_request(request.params)
            yield BridgeResponse(id=request.id, ok=True, result=result.to_dict()).to_dict()
            return

        if request.command == BridgeCommand.GENERATE_PLAYLIST:
            yield started_event(request.id, command=request.command.value).to_dict()
            result = self._generate_playlist(request.id, request.params)
            yield completed_event(request.id, summary=result.to_dict()).to_dict()
            yield BridgeResponse(id=request.id, ok=True, result=result.to_dict()).to_dict()
            return

        if request.command == BridgeCommand.IMPORT_PLAYLIST:
            yield started_event(request.id, command=request.command.value).to_dict()
            final_result: ImportPlaylistResult | None = None
            for item in self._import_playlist_stream(request.id, request.params):
                if isinstance(item, BridgeEvent):
                    yield item.to_dict()
                else:
                    final_result = item
            if final_result is None:
                raise BridgeError(BridgeErrorCode.ENGINE_ERROR, "Import finished without a result.")
            yield completed_event(request.id, summary=final_result.to_dict()).to_dict()
            yield BridgeResponse(id=request.id, ok=True, result=final_result.to_dict()).to_dict()
            return

        if request.command == BridgeCommand.CONTINUE_MANUAL_ACQUISITION:
            if self.backend is None or not hasattr(self.backend, "continue_manual_acquisition_stream"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend d'import non configuré.")
            session_id = str(request.params.get("import_session_id", "")).strip()
            begin_session(session_id)
            manual_continue_trace(
                f"ENTER json_rpc CONTINUE_MANUAL_ACQUISITION request_id={request.id} params={json.dumps(request.params, ensure_ascii=False)}"
            )
            yield started_event(request.id, command=request.command.value).to_dict()
            final_result: ImportPlaylistResult | None = None
            for item in self.backend.continue_manual_acquisition_stream(request.params):
                if isinstance(item, BridgeEvent):
                    yield item.to_dict()
                else:
                    final_result = item
            if final_result is None:
                raise BridgeError(BridgeErrorCode.ENGINE_ERROR, "Reprise d'import sans résultat.")
            manual_continue_trace("RETURN json_rpc CONTINUE_MANUAL_ACQUISITION — yielding final response")
            yield completed_event(request.id, summary=final_result.to_dict()).to_dict()
            yield BridgeResponse(
                id=request.id,
                ok=True,
                result={"acknowledged": True, "import": final_result.to_dict()["import"]},
            ).to_dict()
            return

        if request.command == BridgeCommand.PROBE_MANUAL_ACQUISITION:
            if self.backend is None or not hasattr(self.backend, "probe_manual_acquisition"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend d'import non configuré.")
            session_id = str(request.params.get("import_session_id", "")).strip()
            begin_session(session_id)
            manual_continue_trace(
                f"ENTER json_rpc PROBE_MANUAL_ACQUISITION request_id={request.id} params={json.dumps(request.params, ensure_ascii=False)}"
            )
            result = self.backend.probe_manual_acquisition(request.params)
            manual_continue_trace(
                f"RETURN json_rpc PROBE_MANUAL_ACQUISITION found={result.get('found')} workflow_phase={result.get('workflow_phase')}"
            )
            yield BridgeResponse(id=request.id, ok=True, result=result).to_dict()
            return

        if request.command == BridgeCommand.RETRY_IMPORT_TRACKS:
            if self.backend is None or not hasattr(self.backend, "retry_import_tracks_stream"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend de réessai d'import non configuré.")
            yield started_event(request.id, command=request.command.value).to_dict()
            final_result: ImportPlaylistResult | None = None
            playlist = _playlist_from_params(request.params)
            track_indices = [int(value) for value in request.params.get("track_indices", [])]
            existing_results = _track_add_results_from_params(request.params)
            history_session_id_raw = request.params.get("history_session_id")
            history_session_id = (
                str(history_session_id_raw).strip() if history_session_id_raw else None
            ) or None
            for item in self.backend.retry_import_tracks_stream(
                playlist,
                track_indices=track_indices,
                request_id=request.id,
                existing_results=existing_results,
                history_session_id=history_session_id,
            ):
                if isinstance(item, BridgeEvent):
                    yield item.to_dict()
                else:
                    final_result = item
            if final_result is None:
                raise BridgeError(BridgeErrorCode.ENGINE_ERROR, "Réessai terminé sans résultat.")
            yield completed_event(request.id, summary=final_result.to_dict()).to_dict()
            yield BridgeResponse(id=request.id, ok=True, result=final_result.to_dict()).to_dict()
            return

        if request.command == BridgeCommand.DIAGNOSTICS:
            result = self._diagnostics()
            yield BridgeResponse(id=request.id, ok=True, result=result.to_dict()).to_dict()
            return

        if request.command == BridgeCommand.LIST_HISTORY:
            if self.backend is None or not hasattr(self.backend, "list_history"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend d'historique non configuré.")
            sessions = self.backend.list_history()
            yield BridgeResponse(id=request.id, ok=True, result={"sessions": list(sessions)}).to_dict()
            return

        if request.command == BridgeCommand.GET_HISTORY_SESSION:
            if self.backend is None or not hasattr(self.backend, "get_history_session"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend d'historique non configuré.")
            session_id = str(request.params.get("session_id", "")).strip()
            if not session_id:
                raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "session_id est requis.")
            session = self.backend.get_history_session(session_id)
            yield BridgeResponse(id=request.id, ok=True, result={"session": session}).to_dict()
            return

        if request.command == BridgeCommand.DELETE_HISTORY_SESSION:
            if self.backend is None or not hasattr(self.backend, "delete_history_session"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend d'historique non configuré.")
            session_id = str(request.params.get("session_id", "")).strip()
            if not session_id:
                raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "session_id est requis.")
            deleted = bool(self.backend.delete_history_session(session_id))
            yield BridgeResponse(id=request.id, ok=True, result={"deleted": deleted}).to_dict()
            return

        if request.command == BridgeCommand.CLEAR_HISTORY:
            if self.backend is None or not hasattr(self.backend, "clear_history"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend d'historique non configuré.")
            cleared = bool(self.backend.clear_history())
            yield BridgeResponse(id=request.id, ok=True, result={"cleared": cleared}).to_dict()
            return

        if request.command == BridgeCommand.EXPORT_HISTORY_SESSION:
            if self.backend is None or not hasattr(self.backend, "export_history_session"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend d'historique non configuré.")
            session_id = str(request.params.get("session_id", "")).strip()
            if not session_id:
                raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "session_id est requis.")
            exported = self.backend.export_history_session(session_id)
            yield BridgeResponse(id=request.id, ok=True, result={"export": exported}).to_dict()
            return

        if request.command == BridgeCommand.REPLAY_GENERATION:
            if self.backend is None or not hasattr(self.backend, "replay_generation"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend de replay non configuré.")
            session_id = str(request.params.get("session_id", "")).strip()
            if not session_id:
                raise BridgeError(BridgeErrorCode.INVALID_REQUEST, "session_id est requis.")
            yield started_event(request.id, command=request.command.value).to_dict()
            result = self.backend.replay_generation(session_id, request_id=request.id)
            yield completed_event(request.id, summary=result.to_dict()).to_dict()
            yield BridgeResponse(id=request.id, ok=True, result=result.to_dict()).to_dict()
            return

        if request.command == BridgeCommand.AUTOCOMPLETE_SEARCH:
            if self.backend is None or not hasattr(self.backend, "autocomplete_search"):
                raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend d'autocomplete non configuré.")
            result = self.backend.autocomplete_search(request.params)
            yield BridgeResponse(id=request.id, ok=True, result=result.to_dict()).to_dict()
            return

        raise BridgeError(
            BridgeErrorCode.UNKNOWN_COMMAND,
            f"Commande inconnue : {request.command.value}",
        )

    def _list_providers(self) -> ListProvidersResult:
        if self.backend is not None:
            return self.backend.list_providers()
        return ListProvidersResult(providers=default_provider_options())

    def _validate_generation_request(self, params: dict[str, Any]) -> ValidateGenerationRequestResult:
        generation_request = _parse_generation_request_from_params(params)
        validation = validate_playlist_generation_request(generation_request)
        return ValidateGenerationRequestResult(valid=validation.is_valid, errors=validation.errors)

    def _generate_playlist(self, request_id: str, params: dict[str, Any]) -> GeneratePlaylistResult:
        if self.backend is None:
            raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend de génération non configuré.")
        generation_request = _parse_generation_request_from_params(params)
        validation = validate_playlist_generation_request(generation_request)
        if not validation.is_valid:
            raise BridgeError(
                BridgeErrorCode.VALIDATION_FAILED,
                "Requête de génération invalide.",
                details=tuple((error.field, error.message) for error in validation.errors),
            )
        try:
            try:
                return self.backend.generate_playlist(generation_request, request_id=request_id)
            except TypeError:
                # Backward compatibility for lightweight test backends.
                return self.backend.generate_playlist(generation_request)
        except BridgeError:
            raise
        except Exception as exc:
            raise BridgeError(BridgeErrorCode.ENGINE_ERROR, str(exc)) from exc

    def _import_playlist_stream(
        self,
        request_id: str,
        params: dict[str, Any],
    ) -> Iterator[BridgeEvent | ImportPlaylistResult]:
        if self.backend is None:
            raise BridgeError(BridgeErrorCode.NOT_CONFIGURED, "Backend d'import non configuré.")
        playlist = _playlist_from_params(params)
        sync = bool(params.get("sync", True))
        write_json_diagnostics = bool(params.get("write_json_diagnostics", True))
        history_session_id_raw = params.get("history_session_id")
        history_session_id = str(history_session_id_raw).strip() if history_session_id_raw else None
        try:
            try:
                yield from self.backend.import_playlist_stream(
                    playlist,
                    sync=sync,
                    write_json_diagnostics=write_json_diagnostics,
                    request_id=request_id,
                    history_session_id=history_session_id,
                )
            except TypeError:
                yield from self.backend.import_playlist_stream(
                    playlist,
                    sync=sync,
                    write_json_diagnostics=write_json_diagnostics,
                    request_id=request_id,
                )
        except BridgeError:
            raise
        except Exception as exc:
            raise BridgeError(BridgeErrorCode.ENGINE_ERROR, str(exc)) from exc

    def _diagnostics(self) -> DiagnosticsResult:
        if self.backend is not None:
            return self.backend.diagnostics()
        return DiagnosticsResult(engine_version=__version__)


def decode_json_line(line: str) -> dict[str, Any]:
    line = line.strip()
    if not line:
        raise InvalidBridgeRequestError("Empty JSON line.")
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise InvalidBridgeRequestError(f"JSON invalide : {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise InvalidBridgeRequestError("JSON line must decode to an object.")
    return payload


def process_json_line(bridge: EngineBridge, line: str) -> list[str]:
    try:
        request = decode_json_line(line)
    except InvalidBridgeRequestError as exc:
        return [
            encode_json_line(
                _error_response("unknown", exc.code, exc.message, details=exc.details).to_dict(),
            )
        ]
    return [encode_json_line(message) for message in bridge.handle(request)]


def encode_json_line(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _parse_generation_request_from_params(params: dict[str, Any]) -> PlaylistGenerationRequest:
    request_data = params.get("request")
    if not isinstance(request_data, dict):
        raise InvalidBridgeRequestError("Paramètre 'request' manquant ou invalide.")
    return playlist_generation_request_from_dict(request_data)


def _playlist_from_params(params: dict[str, Any]) -> PlaylistDefinition:
    playlist_data = params.get("playlist")
    if not isinstance(playlist_data, dict):
        raise InvalidBridgeRequestError("Paramètre 'playlist' manquant ou invalide.")

    name = str(playlist_data.get("name", "")).strip()
    if not name:
        raise InvalidBridgeRequestError("Le nom de playlist est requis.")

    description = str(playlist_data.get("description", ""))
    sections_data = playlist_data.get("sections")
    if not isinstance(sections_data, list) or not sections_data:
        raise InvalidBridgeRequestError("Au moins une section est requise.")

    sections: list[PlaylistSection] = []
    for section_data in sections_data:
        if not isinstance(section_data, dict):
            raise InvalidBridgeRequestError("Section invalide.")
        section_name = str(section_data.get("name", "Playlist"))
        songs = section_data.get("songs", section_data.get("tracks", []))
        if not isinstance(songs, list):
            raise InvalidBridgeRequestError("Liste de morceaux invalide.")
        tracks: list[TrackRef] = []
        for song in songs:
            if not isinstance(song, dict):
                continue
            artist = str(song.get("artist", "")).strip()
            title = str(song.get("title", "")).strip()
            if artist and title:
                tracks.append(TrackRef(artist=artist, title=title, section=section_name))
        sections.append(PlaylistSection(name=section_name, tracks=tuple(tracks)))

    return PlaylistDefinition(name=name, sections=tuple(sections), description=description)


def _track_add_results_from_params(params: dict[str, Any]) -> list[TrackAddResult] | None:
    raw = params.get("existing_outcomes")
    if not isinstance(raw, list) or not raw:
        return None

    results: list[TrackAddResult] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        artist = str(item.get("artist", "")).strip()
        title = str(item.get("title", "")).strip()
        if not artist or not title:
            continue
        section = str(item.get("section", "Playlist")).strip() or "Playlist"
        status_raw = str(item.get("status", "")).strip().lower()
        status = {
            "added": TrackAddStatus.ADDED,
            "skipped": TrackAddStatus.SKIPPED,
            "not_found": TrackAddStatus.NOT_FOUND,
            "error": TrackAddStatus.ERROR,
            "acquiring": TrackAddStatus.NOT_FOUND,
            "pending": TrackAddStatus.NOT_FOUND,
        }.get(status_raw, TrackAddStatus.ERROR)
        message = str(item.get("message", "")).strip()
        results.append(
            TrackAddResult(
                track=TrackRef(artist=artist, title=title, section=section),
                status=status,
                error=message,
            )
        )
    return results or None


def _error_response(
    request_id: str,
    code: BridgeErrorCode,
    message: str,
    *,
    details: tuple[tuple[str, str], ...] = (),
) -> BridgeResponse:
    error = BridgeError(code, message, details=details)
    return BridgeResponse(id=request_id or "unknown", ok=False, error=error.to_dict())
