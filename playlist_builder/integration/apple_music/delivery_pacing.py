from __future__ import annotations

import time
from typing import TYPE_CHECKING

from playlist_builder.catalog.retry_policy import RetryPolicy

if TYPE_CHECKING:
    from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient

DELIVERY_BATCH_PACE_SECONDS = 0.4
DELIVERY_ADD_RETRY_POLICY = RetryPolicy(
    base_min_delay=0.6,
    increment=0.4,
    max_min_delay=2.0,
    max_attempts=4,
    max_total_wait=12.0,
)
PLAYLIST_SETTLE_TIMEOUT_SECONDS = 20.0
PLAYLIST_SETTLE_POLL_SECONDS = 0.75
CLEAR_CONFIRM_TIMEOUT_SECONDS = 15.0


def pace_between_delivery_batches(batch_index: int) -> None:
    if batch_index <= 0:
        return
    time.sleep(DELIVERY_BATCH_PACE_SECONDS)


def wait_for_playlist_track_count(
    applescript: AppleScriptClient,
    playlist_name: str,
    *,
    minimum_count: int,
    timeout_seconds: float = PLAYLIST_SETTLE_TIMEOUT_SECONDS,
    poll_seconds: float = PLAYLIST_SETTLE_POLL_SECONDS,
) -> bool:
    if minimum_count <= 0:
        return True
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            count = int(applescript.count_playlist_tracks(playlist_name))
        except (TypeError, ValueError):
            return False
        if count >= minimum_count:
            return True
        time.sleep(poll_seconds)
    return False


def wait_for_playlist_cleared(
    applescript: AppleScriptClient,
    playlist_name: str,
    *,
    timeout_seconds: float = CLEAR_CONFIRM_TIMEOUT_SECONDS,
    poll_seconds: float = PLAYLIST_SETTLE_POLL_SECONDS,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            count = int(applescript.count_playlist_tracks(playlist_name))
        except (TypeError, ValueError):
            return False
        if count == 0:
            return True
        time.sleep(poll_seconds)
    return False


def retry_delay_for_attempt(attempt: int, policy: RetryPolicy = DELIVERY_ADD_RETRY_POLICY) -> float:
    return policy.delay_for_attempt(attempt)
