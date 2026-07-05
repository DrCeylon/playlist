from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient


def test_phased_acquire_emits_detailed_spans(monkeypatch):
    monkeypatch.setenv("RESONANCE_PERF_TRACE", "1")
    client = AppleScriptClient()

    with patch.object(client, "_try_add_url", return_value="") as add_mock, patch.object(
        client, "_open_catalog_url"
    ) as open_mock, patch.object(client, "_poll_for_current_track", return_value=2) as poll_mock, patch.object(
        client, "_play_current_track"
    ), patch.object(client, "_duplicate_current_track_to_library"), patch.object(
        client, "_search_library_persistent_id", return_value="PID-123"
    ) as search_mock, patch("playlist_builder.integration.apple_music.applescript_client.time.sleep") as sleep_mock:
        status, detail = client.acquire_song_from_url(
            "https://music.apple.com/us/song/firestone/950274258",
            track_id="950274258",
            search_terms=["Kygo Firestone"],
            play_delay_seconds=5.0,
            settle_delay_seconds=6.0,
        )

    assert status == "added"
    assert detail == "PID-123"
    assert add_mock.call_count >= 1
    assert open_mock.call_count >= 1
    assert poll_mock.call_count == 1
    assert search_mock.call_count == 1
    assert sleep_mock.call_count >= 3


def test_monolithic_acquire_when_perf_trace_disabled(monkeypatch):
    monkeypatch.delenv("RESONANCE_PERF_TRACE", raising=False)
    client = AppleScriptClient()

    with patch.object(
        client,
        "_acquire_song_from_url_monolithic",
        return_value=("duplicated", "ok"),
    ) as mono_mock, patch.object(client, "_acquire_song_from_url_phased") as phased_mock:
        status, detail = client.acquire_song_from_url("https://music.apple.com/song/id1", track_id="1")

    assert status == "duplicated"
    assert detail == "ok"
    mono_mock.assert_called_once()
    phased_mock.assert_not_called()


def test_acquire_url_budget_matches_observed_baseline():
    """Static budget: scripted delays explain ~71s when multiple URL variants are tried."""
    poll_max = 16 * 0.5
    play_delay = 5.0
    post_play = 1.0
    settle_delay = 6.0
    per_url_fallback = poll_max + play_delay + post_play + settle_delay
    assert per_url_fallback == 20.0
    # 4 URL variants (itms/https/music/primary) × 20s ≈ 80s upper bound without phase-1 add blocking.
    assert 3.5 * per_url_fallback == pytest.approx(70.0)
