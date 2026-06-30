from __future__ import annotations

import json

import pytest

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.bridge.commands import (
    BridgeCommand,
    BridgeResponse,
    ListProvidersResult,
    ValidateGenerationRequestResult,
    parse_bridge_request,
    playlist_generation_request_from_dict,
)
from playlist_builder.ui.bridge.errors import InvalidBridgeRequestError
from playlist_builder.ui.shared.dto import EnergyCurveProfile, ExclusionKind, ProviderOption
from playlist_builder.ui.shared.validation import dto_to_dict


def test_parse_bridge_request():
    request = parse_bridge_request(
        {"id": "1", "command": "list_providers", "params": {}},
    )
    assert request.id == "1"
    assert request.command == BridgeCommand.LIST_PROVIDERS


def test_parse_bridge_request_unknown_command_raises():
    with pytest.raises(InvalidBridgeRequestError, match="Unknown bridge command"):
        parse_bridge_request({"id": "1", "command": "not_a_command"})


def test_playlist_generation_request_from_dict_round_trip():
    raw = {
        "name": "Pool Party",
        "provider_id": "apple_music",
        "seeds": [{"artist": "Kygo", "title": "Firestone", "weight": 1.0}],
        "keywords": ["tropical"],
        "target_track_count": 20,
        "energy_curve": {"profile": "rising", "chapter_labels": ["Warm Up"]},
        "exclusions": [{"kind": "genre", "value": "reggaeton"}],
    }
    request = playlist_generation_request_from_dict(raw)
    assert request.name == "Pool Party"
    assert request.provider_id == ProviderId.APPLE_MUSIC
    assert request.seeds[0].artist == "Kygo"
    assert request.energy_curve.profile == EnergyCurveProfile.RISING
    assert request.exclusions[0].kind == ExclusionKind.GENRE

    serialized = dto_to_dict(request)
    json.dumps(serialized)
    assert serialized["provider_id"] == "apple_music"


def test_list_providers_result_serialization():
    payload = ListProvidersResult(
        providers=(
            ProviderOption(
                provider_id=ProviderId.APPLE_MUSIC,
                display_name="Apple Music",
                is_available=True,
            ),
        )
    ).to_dict()
    assert payload["providers"][0]["display_name"] == "Apple Music"


def test_validate_generation_request_result_serialization():
    payload = ValidateGenerationRequestResult(valid=False, errors=()).to_dict()
    assert payload["valid"] is False
    assert payload["errors"] == []


def test_bridge_response_to_dict_success():
    response = BridgeResponse(id="42", ok=True, result={"ok": True})
    data = response.to_dict()
    assert data["type"] == "response"
    assert data["ok"] is True
    assert data["result"]["ok"] is True


def test_bridge_response_to_dict_error():
    response = BridgeResponse(id="42", ok=False, error={"code": "engine_error", "message": "boom"})
    data = response.to_dict()
    assert data["ok"] is False
    assert data["error"]["code"] == "engine_error"
