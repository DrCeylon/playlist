from __future__ import annotations

import sys
import time
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from playlist_builder.core.applescript import apple_escape, run_applescript
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.apple_music.constants import FIELD_DELIMITER


class AcquisitionStrategyId(StrEnum):
    ADD_URL_DIRECT = "S1_add_url_direct"
    OPEN_LOCATION_APPLESCRIPT = "S2_open_location_applescript"
    SYSTEM_EVENTS_ADD_TO_LIBRARY = "S3_system_events_add_to_library"
    MANUAL_FALLBACK = "S4_manual_fallback"


@dataclass(frozen=True, slots=True)
class AcquisitionStrategyResult:
    strategy_id: str
    strategy_name: str
    success: bool
    duration_ms: int
    applescript_error: str = ""
    persistent_id: str = ""
    found_in_library: bool = False
    music_app_activated: bool = False
    library_search_terms: tuple[str, ...] = ()
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["library_search_terms"] = list(self.library_search_terms)
        return payload


@dataclass(frozen=True, slots=True)
class AcquisitionExperimentInput:
    url: str
    track_id: str = ""
    artist: str = ""
    title: str = ""
    search_terms: tuple[str, ...] = ()
    play_delay_seconds: float = 5.0
    settle_delay_seconds: float = 6.0
    activate_music: bool = False


def default_search_terms(artist: str, title: str) -> tuple[str, ...]:
    terms: list[str] = []
    artist = artist.strip()
    title = title.strip()
    if artist and title:
        terms.append(f"{artist} {title}")
    if title:
        terms.append(title)
    if artist:
        terms.append(artist)
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        key = term.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(term)
    return tuple(unique)


def run_acquisition_experiment(
    experiment_input: AcquisitionExperimentInput,
    *,
    strategies: list[AcquisitionStrategyId] | None = None,
    manual_prompt: bool = True,
) -> list[AcquisitionStrategyResult]:
    if sys.platform != "darwin":
        raise RuntimeError("Les expériences d'acquisition Apple Music nécessitent macOS.")

    selected = strategies or list(AcquisitionStrategyId)
    terms = experiment_input.search_terms or default_search_terms(
        experiment_input.artist,
        experiment_input.title,
    )
    urls = AppleScriptClient._catalog_acquire_urls(experiment_input.url, experiment_input.track_id)

    results: list[AcquisitionStrategyResult] = []
    for strategy_id in selected:
        if strategy_id == AcquisitionStrategyId.ADD_URL_DIRECT:
            results.append(_run_add_url_direct(urls, terms, experiment_input.activate_music))
        elif strategy_id == AcquisitionStrategyId.OPEN_LOCATION_APPLESCRIPT:
            results.append(
                _run_open_location_applescript(
                    urls,
                    terms,
                    activate_music=experiment_input.activate_music,
                    play_delay_seconds=experiment_input.play_delay_seconds,
                    settle_delay_seconds=experiment_input.settle_delay_seconds,
                )
            )
        elif strategy_id == AcquisitionStrategyId.SYSTEM_EVENTS_ADD_TO_LIBRARY:
            results.append(
                _run_system_events_add_to_library(
                    urls,
                    terms,
                    activate_music=True,
                )
            )
        elif strategy_id == AcquisitionStrategyId.MANUAL_FALLBACK:
            results.append(
                _run_manual_fallback(
                    urls,
                    terms,
                    activate_music=True,
                    manual_prompt=manual_prompt,
                )
            )
    return results


def _ensure_music_running(*, activate: bool) -> None:
    if activate:
        run_applescript('tell application "Music" to activate', operation="experiment_ensure_running")
        return
    run_applescript(
        '''
tell application "Music"
    if it is not running then
        launch
    end if
end tell
''',
        operation="experiment_ensure_running",
    )


def _search_library_persistent_id(search_terms: tuple[str, ...]) -> tuple[str, bool]:
    for term in search_terms:
        normalized = term.strip()
        if not normalized:
            continue
        escaped = apple_escape(normalized)
        try:
            output = run_applescript(
                f'''
tell application "Music"
    set searchResults to (search library playlist 1 for "{escaped}" only songs)
    if (count of searchResults) > 0 then
        return (persistent ID of item 1 of searchResults) as text
    end if
    return ""
end tell
''',
                operation="experiment_library_search",
            )
        except RuntimeError:
            continue
        persistent_id = output.strip()
        if persistent_id:
            return persistent_id, True
    return "", False


def _run_add_url_direct(
    urls: list[str],
    search_terms: tuple[str, ...],
    activate_music: bool,
) -> AcquisitionStrategyResult:
    started = time.perf_counter()
    error_messages: list[str] = []
    persistent_id = ""
    activated = bool(activate_music)
    url_attempts: list[dict[str, str]] = []

    try:
        _ensure_music_running(activate=activate_music)
        for index, track_url in enumerate(urls, start=1):
            escaped = apple_escape(track_url)
            try:
                output = run_applescript(
                    f'''
tell application "Music"
    try
        set addedItems to add "{escaped}"
        if (count of addedItems) > 0 then
            return (persistent ID of item 1 of addedItems) as text
        end if
    on error errMsg
        return "error:{FIELD_DELIMITER}" & errMsg
    end try
    return ""
end tell
''',
                    operation="experiment_add_url",
                )
            except RuntimeError as exc:
                message = str(exc)
                error_messages.append(message)
                url_attempts.append({"url_index": str(index), "result": "error", "detail": message})
                continue

            if output.startswith(f"error:{FIELD_DELIMITER}"):
                message = output.split(FIELD_DELIMITER, 1)[-1]
                error_messages.append(message)
                url_attempts.append({"url_index": str(index), "result": "applescript_error", "detail": message})
                continue

            if output.strip():
                persistent_id = output.strip()
                url_attempts.append({"url_index": str(index), "result": "added", "persistent_id": persistent_id})
                break
            url_attempts.append({"url_index": str(index), "result": "empty"})
    except RuntimeError as exc:
        error_messages.append(str(exc))

    found_in_library = False
    if persistent_id:
        found_in_library = True
    else:
        persistent_id, found_in_library = _search_library_persistent_id(search_terms)

    duration_ms = int((time.perf_counter() - started) * 1000)
    return AcquisitionStrategyResult(
        strategy_id=AcquisitionStrategyId.ADD_URL_DIRECT.value,
        strategy_name="Add URL direct",
        success=bool(persistent_id) and found_in_library,
        duration_ms=duration_ms,
        applescript_error=" | ".join(error_messages),
        persistent_id=persistent_id,
        found_in_library=found_in_library,
        music_app_activated=activated,
        library_search_terms=search_terms,
        notes="Tente add (trackUrl) pour chaque variante d'URL sans open/play/duplicate.",
        metadata={"url_attempts": url_attempts, "url_count": len(urls)},
    )


def _run_open_location_applescript(
    urls: list[str],
    search_terms: tuple[str, ...],
    *,
    activate_music: bool,
    play_delay_seconds: float,
    settle_delay_seconds: float,
) -> AcquisitionStrategyResult:
    started = time.perf_counter()
    error_messages: list[str] = []
    persistent_id = ""
    activated = bool(activate_music)
    path_notes: list[str] = []

    try:
        _ensure_music_running(activate=activate_music)
        for index, track_url in enumerate(urls, start=1):
            escaped = apple_escape(track_url)
            try:
                run_applescript(
                    f'tell application "Music" to open location "{escaped}"',
                    operation="experiment_open_location",
                )
            except RuntimeError as exc:
                error_messages.append(f"open_location[{index}]: {exc}")
                continue

            for _ in range(16):
                time.sleep(0.5)
                try:
                    probe = run_applescript(
                        '''
tell application "Music"
    try
        set _ to current track
        return "yes"
    on error
        return "no"
    end try
end tell
''',
                        operation="experiment_probe_current_track",
                    )
                except RuntimeError as exc:
                    error_messages.append(f"probe_current_track[{index}]: {exc}")
                    break
                if probe.strip().casefold() == "yes":
                    break

            time.sleep(max(0.0, play_delay_seconds))
            try:
                run_applescript('tell application "Music" to play', operation="experiment_play")
            except RuntimeError as exc:
                error_messages.append(f"play[{index}]: {exc}")

            time.sleep(1.0)
            try:
                run_applescript(
                    'tell application "Music" to duplicate current track to source "Library"',
                    operation="experiment_duplicate_to_library",
                )
                path_notes.append(f"duplicate_ok_url_{index}")
            except RuntimeError as exc:
                error_messages.append(f"duplicate[{index}]: {exc}")
                continue

            time.sleep(max(0.0, settle_delay_seconds))
            persistent_id, found = _search_library_persistent_id(search_terms)
            if found and persistent_id:
                path_notes.append(f"library_hit_url_{index}")
                break
    except RuntimeError as exc:
        error_messages.append(str(exc))

    found_in_library = bool(persistent_id)
    if not found_in_library:
        persistent_id, found_in_library = _search_library_persistent_id(search_terms)

    duration_ms = int((time.perf_counter() - started) * 1000)
    return AcquisitionStrategyResult(
        strategy_id=AcquisitionStrategyId.OPEN_LOCATION_APPLESCRIPT.value,
        strategy_name="Open location + play + duplicate (production path)",
        success=found_in_library and bool(persistent_id),
        duration_ms=duration_ms,
        applescript_error=" | ".join(error_messages),
        persistent_id=persistent_id,
        found_in_library=found_in_library,
        music_app_activated=activated,
        library_search_terms=search_terms,
        notes="Reproduit le fallback PR9 : open → poll → play → duplicate → search.",
        metadata={"path_notes": path_notes, "url_count": len(urls)},
    )


def _run_system_events_add_to_library(
    urls: list[str],
    search_terms: tuple[str, ...],
    *,
    activate_music: bool,
) -> AcquisitionStrategyResult:
    started = time.perf_counter()
    error_messages: list[str] = []
    menu_attempts: list[str] = []
    activated = bool(activate_music)

    try:
        _ensure_music_running(activate=activate_music)
        if urls:
            escaped = apple_escape(urls[0])
            run_applescript(
                f'tell application "Music" to open location "{escaped}"',
                operation="experiment_open_location_for_ui",
            )
        time.sleep(2.0)

        menu_labels = (
            "Add to Library",
            "Ajouter à la bibliothèque",
            "Add to Library…",
            "Ajouter à la bibliothèque…",
        )
        clicked = False
        for label in menu_labels:
            escaped_label = apple_escape(label)
            script = f'''
tell application "Music" to activate
delay 0.5
tell application "System Events"
    tell process "Music"
        try
            click menu item "{escaped_label}" of menu "Song" of menu bar item "Song" of menu bar 1
            return "clicked"
        on error errMsg
            return "error:{escaped_label}:" & errMsg
        end try
    end tell
end tell
'''
            try:
                output = run_applescript(script, operation="experiment_system_events_add")
            except RuntimeError as exc:
                error_messages.append(str(exc))
                menu_attempts.append(f"{label}:exception")
                continue
            menu_attempts.append(f"{label}:{output.strip()}")
            if output.strip() == "clicked":
                clicked = True
                break
            if output.startswith("error:"):
                error_messages.append(output.strip())

        if not clicked:
            error_messages.append("Aucun libellé de menu « Add to Library » n'a pu être activé.")

        time.sleep(4.0)
    except RuntimeError as exc:
        error_messages.append(str(exc))

    persistent_id, found_in_library = _search_library_persistent_id(search_terms)
    duration_ms = int((time.perf_counter() - started) * 1000)
    return AcquisitionStrategyResult(
        strategy_id=AcquisitionStrategyId.SYSTEM_EVENTS_ADD_TO_LIBRARY.value,
        strategy_name="System Events — menu Add to Library",
        success=found_in_library and bool(persistent_id),
        duration_ms=duration_ms,
        applescript_error=" | ".join(error_messages),
        persistent_id=persistent_id,
        found_in_library=found_in_library,
        music_app_activated=activated,
        library_search_terms=search_terms,
        notes="Contournement UI documenté par la communauté Apple ; nécessite accessibilité macOS.",
        metadata={"menu_attempts": menu_attempts},
    )


def _run_manual_fallback(
    urls: list[str],
    search_terms: tuple[str, ...],
    *,
    activate_music: bool,
    manual_prompt: bool,
) -> AcquisitionStrategyResult:
    started = time.perf_counter()
    error_messages: list[str] = []
    activated = bool(activate_music)
    notes = "Workflow manuel Resonance : ouvrir Music, ajouter à la bibliothèque, puis sonder library playlist 1."

    try:
        _ensure_music_running(activate=activate_music)
        if urls:
            escaped = apple_escape(urls[0])
            run_applescript(
                f'tell application "Music" to open location "{escaped}"',
                operation="experiment_manual_open",
            )
        if manual_prompt:
            print(
                "\n[S4_manual_fallback] Ajoutez le morceau à votre bibliothèque dans Music.app, "
                "puis appuyez sur Entrée pour sonder la bibliothèque…",
                flush=True,
            )
            try:
                input()
            except EOFError:
                notes += " (mode non interactif — sonde immédiate sans attente utilisateur)"
        else:
            notes += " (manual_prompt désactivé — sonde immédiate)"
            time.sleep(2.0)
    except RuntimeError as exc:
        error_messages.append(str(exc))

    persistent_id, found_in_library = _search_library_persistent_id(search_terms)
    duration_ms = int((time.perf_counter() - started) * 1000)
    return AcquisitionStrategyResult(
        strategy_id=AcquisitionStrategyId.MANUAL_FALLBACK.value,
        strategy_name="Fallback manuel (workflow Resonance 5.2)",
        success=found_in_library and bool(persistent_id),
        duration_ms=duration_ms,
        applescript_error=" | ".join(error_messages),
        persistent_id=persistent_id,
        found_in_library=found_in_library,
        music_app_activated=activated,
        library_search_terms=search_terms,
        notes=notes,
        metadata={"manual_prompt": manual_prompt},
    )


def summarize_results(results: list[AcquisitionStrategyResult]) -> dict[str, Any]:
    ranked = sorted(
        [result for result in results if result.success],
        key=lambda item: item.duration_ms,
    )
    return {
        "strategy_count": len(results),
        "success_count": sum(1 for result in results if result.success),
        "fastest_success": ranked[0].to_dict() if ranked else None,
        "failures": [result.to_dict() for result in results if not result.success],
    }
