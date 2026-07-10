from __future__ import annotations

import json

import pytest

from playlist_builder.canonical.enums import ConfidenceLevel, ProviderId
from playlist_builder.ui.shared.dto import (
    DiagnosticEvent,
    DiagnosticLevel,
    EnergyCurveOption,
    EnergyCurveProfile,
    ExclusionKind,
    ExclusionRule,
    ImportPhase,
    ImportProgressState,
    ImportResultState,
    ImportTrackOutcome,
    ImportTrackStatus,
    PlaylistGenerationRequest,
    PlaylistGenerationResult,
    ProviderOption,
    SeedReference,
    ThemeOption,
    UserPreferences,
    default_provider_options,
)
from playlist_builder.ui.shared.dto.generation import GeneratedSectionPreview, GeneratedTrackPreview
from playlist_builder.ui.shared.navigation import AppRoute
from playlist_builder.ui.shared.state import UiScreenState
from playlist_builder.ui.shared.validation import dto_to_dict


def _valid_request(**overrides) -> PlaylistGenerationRequest:
    base = dict(
        name="Orlando Pool Party",
        provider_id=ProviderId.APPLE_MUSIC,
        seeds=(SeedReference(artist="Kygo", title="Firestone"),),
        target_track_count=50,
        energy_curve=EnergyCurveOption(profile=EnergyCurveProfile.RISING),
    )
    base.update(overrides)
    return PlaylistGenerationRequest(**base)


def test_playlist_generation_request_construction():
    request = _valid_request()
    assert request.name == "Orlando Pool Party"
    assert request.provider_id == ProviderId.APPLE_MUSIC
    assert request.seeds[0].label == "Kygo — Firestone"


def test_playlist_generation_result_track_count():
    result = PlaylistGenerationResult(
        playlist_name="Test",
        sections=(
            GeneratedSectionPreview(
                name="A",
                tracks=(
                    GeneratedTrackPreview("Kygo", "Firestone", "A", 92.0, ConfidenceLevel.HIGH),
                    GeneratedTrackPreview("Avicii", "Levels", "A", 80.0),
                ),
            ),
            GeneratedSectionPreview(
                name="B",
                tracks=(GeneratedTrackPreview("Kyo", "Dernière danse", "B", 75.0),),
            ),
        ),
        average_score=82.3,
    )
    assert result.track_count == 3


def test_provider_options_catalog_lists_planned_providers():
    options = default_provider_options()
    provider_ids = {option.provider_id for option in options}
    assert ProviderId.APPLE_MUSIC in provider_ids
    assert ProviderId.SPOTIFY in provider_ids
    assert ProviderId.LOCAL_FILES in provider_ids
    assert all(option.is_available is False for option in options)


def test_provider_options_registry_overrides_availability():
    from playlist_builder.app.factory import build_app_context
    from playlist_builder.app.bridge_runtime.provider_platform import provider_options_from_registry

    context = build_app_context()
    options = provider_options_from_registry(context.registry)
    apple = next(option for option in options if option.provider_id == ProviderId.APPLE_MUSIC)
    assert apple.is_available or apple.unavailable_reason
    assert apple.capabilities


def test_theme_option_construction():
    theme = ThemeOption("apple_music_dark", "Apple Music Dark", "#1C1C1E", "#FA2D48")
    assert theme.theme_id == "apple_music_dark"


def test_energy_curve_profiles():
    for profile in (EnergyCurveProfile.RISING, EnergyCurveProfile.MAX_FROM_START, EnergyCurveProfile.RANDOM):
        curve = EnergyCurveOption(profile=profile)
        assert curve.profile == profile


def test_exclusion_kinds_cover_ui_set():
    kinds = {ExclusionKind.ARTIST, ExclusionKind.ALBUM, ExclusionKind.TRACK, ExclusionKind.GENRE, ExclusionKind.MOOD, ExclusionKind.LANGUAGE}
    assert kinds.issubset(set(ExclusionKind))


def test_import_progress_ratio():
    state = ImportProgressState(
        phase=ImportPhase.RESOLVING,
        playlist_name="E2E",
        total_tracks=10,
        processed_tracks=4,
    )
    assert state.progress_ratio == pytest.approx(0.4)


def test_import_result_state_counts():
    outcomes = (
        ImportTrackOutcome("Kygo", "Firestone", "A", ImportTrackStatus.ADDED),
        ImportTrackOutcome("Kyo", "Dernière danse", "A", ImportTrackStatus.NOT_FOUND, "acquisition"),
    )
    result = ImportResultState(playlist_name="E2E", outcomes=outcomes)
    assert result.added_count == 1
    assert result.not_found_count == 1


def test_diagnostic_event_construction():
    event = DiagnosticEvent("resolver", "cache hit", DiagnosticLevel.INFO, "2026-06-30T12:00:00")
    assert event.level == DiagnosticLevel.INFO


def test_user_preferences_defaults():
    prefs = UserPreferences()
    assert prefs.default_provider_id == ProviderId.APPLE_MUSIC
    assert prefs.locale == "fr"


def test_app_route_values():
    assert AppRoute.HOME.value == "home"
    assert AppRoute.PLAYLISTS.value == "playlists"
    assert AppRoute.SYNC.value == "sync"
    assert AppRoute.PROVIDERS.value == "providers"
    assert AppRoute.MANUAL_ACQUISITION.value == "manual_acquisition"


def test_ui_screen_state_values():
    assert UiScreenState.WAITING_FOR_MANUAL_ACQUISITION.value == "waiting_for_manual_acquisition"
    assert UiScreenState.PARTIAL_SUCCESS.value == "partial_success"


def test_dto_serialization_round_trip_json_friendly():
    request = _valid_request(
        exclusions=(ExclusionRule(ExclusionKind.GENRE, "reggaeton", "pool party"),),
        keywords=("tropical",),
    )
    payload = dto_to_dict(request)
    json.dumps(payload)
    assert payload["provider_id"] == "apple_music"
    assert payload["energy_curve"]["profile"] == "rising"
    assert payload["exclusions"][0]["kind"] == "genre"


def test_provider_option_serialization():
    from playlist_builder.app.factory import build_app_context
    from playlist_builder.app.bridge_runtime.provider_platform import provider_options_from_registry

    context = build_app_context()
    option = next(
        item for item in provider_options_from_registry(context.registry) if item.provider_id == ProviderId.APPLE_MUSIC
    )
    payload = dto_to_dict(option)
    assert "catalog_search" in payload["capabilities"]
