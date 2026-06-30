from __future__ import annotations

import json

import pytest

from playlist_builder.ui.bridge.commands import playlist_generation_request_from_dict
from playlist_builder.ui.bridge.errors import InvalidBridgeRequestError
from playlist_builder.ui.bridge.json_rpc import decode_json_line, process_json_line


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        ({"provider_id": "not_a_provider", "seeds": [{"artist": "A", "title": "B"}], "target_track_count": 1}, "provider_id"),
        ({"provider_id": "apple_music", "seeds": "oops", "target_track_count": 1}, "seeds"),
        ({"provider_id": "apple_music", "seeds": ["bad"], "target_track_count": 1}, "seed"),
        (
            {
                "provider_id": "apple_music",
                "seeds": [{"artist": "A", "title": "B"}],
                "exclusions": [{"kind": "not_a_kind", "value": "x"}],
                "target_track_count": 1,
            },
            "exclusion.kind",
        ),
        (
            {
                "provider_id": "apple_music",
                "seeds": [{"artist": "A", "title": "B"}],
                "energy_curve": {"profile": "not_a_profile"},
                "target_track_count": 1,
            },
            "energy_curve.profile",
        ),
        (
            {
                "provider_id": "apple_music",
                "seeds": [{"artist": "A", "title": "B"}],
                "energy_curve": "bad",
                "target_track_count": 1,
            },
            "energy_curve",
        ),
        (
            {
                "provider_id": "apple_music",
                "seeds": [{"artist": "A", "title": "B"}],
                "target_track_count": "many",
            },
            "target_track_count",
        ),
    ],
)
def test_playlist_generation_request_invalid_payload_raises_invalid_request(payload: dict, match: str):
    with pytest.raises(InvalidBridgeRequestError, match=match):
        playlist_generation_request_from_dict(payload)


def test_decode_json_line_invalid_json():
    with pytest.raises(InvalidBridgeRequestError, match="JSON invalide"):
        decode_json_line("{not-json")


def test_process_json_line_invalid_json_returns_error_response():
    from playlist_builder.ui.bridge import JsonRpcEngineBridge

    lines = process_json_line(JsonRpcEngineBridge(), "{not-json")
    payload = json.loads(lines[0])
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_request"
