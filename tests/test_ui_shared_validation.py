from __future__ import annotations

import pytest

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto import (
    EnergyCurveOption,
    EnergyCurveProfile,
    ExclusionKind,
    ExclusionRule,
    PlaylistGenerationRequest,
    SeedReference,
    UserPreferences,
)
from playlist_builder.ui.shared.validation.generation import (
    validate_energy_curve,
    validate_exclusion_rule,
    validate_playlist_generation_request,
    validate_playlist_name,
    validate_provider_id,
    validate_seeds_or_keywords,
    validate_target_size,
    validate_user_preferences,
)


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


def test_validate_playlist_name_ok():
    assert validate_playlist_name("My Playlist").is_valid


def test_validate_playlist_name_missing():
    result = validate_playlist_name("   ")
    assert not result.is_valid
    assert result.errors[0].field == "name"


def test_validate_seeds_or_keywords_requires_one():
  assert validate_seeds_or_keywords((), ()).is_valid is False
  assert validate_seeds_or_keywords((SeedReference(artist="Kygo"),), ()).is_valid
  assert validate_seeds_or_keywords((), ("tropical",)).is_valid


def test_validate_target_size_requires_one():
    assert validate_target_size(None, None).is_valid is False
    assert validate_target_size(50, None).is_valid
    assert validate_target_size(None, 180).is_valid


def test_validate_target_size_positive():
    assert not validate_target_size(0, None).is_valid
    assert not validate_target_size(None, -1).is_valid


def test_validate_provider_id_ok():
    assert validate_provider_id(ProviderId.APPLE_MUSIC).is_valid


def test_validate_exclusion_kinds():
    for kind in ExclusionKind:
        result = validate_exclusion_rule(ExclusionRule(kind, "value"))
        assert result.is_valid, kind


def test_validate_exclusion_empty_value():
    result = validate_exclusion_rule(ExclusionRule(ExclusionKind.ARTIST, "  "))
    assert not result.is_valid


def test_validate_energy_curves_rising_max_random():
    for profile in (EnergyCurveProfile.RISING, EnergyCurveProfile.MAX_FROM_START, EnergyCurveProfile.RANDOM):
        assert validate_energy_curve(EnergyCurveOption(profile=profile)).is_valid


def test_validate_playlist_generation_request_ok():
    assert validate_playlist_generation_request(_valid_request()).is_valid


def test_validate_playlist_generation_request_aggregate_errors():
    request = _valid_request(name="", seeds=(), keywords=(), target_track_count=None, target_duration_minutes=None)
    result = validate_playlist_generation_request(request)
    assert not result.is_valid
    fields = {error.field for error in result.errors}
    assert "name" in fields
    assert "seeds" in fields
    assert "target_track_count" in fields


def test_validate_playlist_generation_request_raises():
    with pytest.raises(ValueError, match="nom"):
        validate_playlist_generation_request(_valid_request(name="")).raise_if_invalid()


def test_validate_user_preferences_ok():
    assert validate_user_preferences(UserPreferences()).is_valid


def test_validate_user_preferences_invalid_locale():
    result = validate_user_preferences(UserPreferences(locale="de"))
    assert not result.is_valid
