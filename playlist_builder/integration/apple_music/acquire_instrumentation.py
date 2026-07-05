from __future__ import annotations

import time

from playlist_builder.infrastructure.perf import perf_record, perf_span, perf_trace_enabled
from playlist_builder.integration.apple_music.constants import FIELD_DELIMITER

# Documented in wiki/Phase-5-3-2-Acquisition-Investigation.md
ACQUIRE_POLL_ITERATIONS = 16
ACQUIRE_POLL_DELAY_SECONDS = 0.5
ACQUIRE_POST_PLAY_DELAY_SECONDS = 1.0
DEFAULT_PLAY_DELAY_SECONDS = 5.0
DEFAULT_SETTLE_DELAY_SECONDS = 6.0


def acquire_song_from_url_with_tracing(
    client,
    url: str,
    *,
    artist: str = "",
    title: str = "",
    track_id: str = "",
    search_terms: list[str] | None = None,
    play_delay_seconds: float = DEFAULT_PLAY_DELAY_SECONDS,
    settle_delay_seconds: float = DEFAULT_SETTLE_DELAY_SECONDS,
    use_phased_instrumentation: bool | None = None,
) -> tuple[str, str]:
    """Dispatch acquisition to monolithic or phased (instrumented) implementation."""
    phased = perf_trace_enabled() if use_phased_instrumentation is None else use_phased_instrumentation
    if phased:
        return client._acquire_song_from_url_phased(
            url,
            artist=artist,
            title=title,
            track_id=track_id,
            search_terms=search_terms,
            play_delay_seconds=play_delay_seconds,
            settle_delay_seconds=settle_delay_seconds,
        )
    return client._acquire_song_from_url_monolithic(
        url,
        artist=artist,
        title=title,
        track_id=track_id,
        search_terms=search_terms,
        play_delay_seconds=play_delay_seconds,
        settle_delay_seconds=settle_delay_seconds,
    )


def record_post_acquisition_settle(settle_delay_seconds: float, *, status: str) -> None:
    if not perf_trace_enabled():
        time.sleep(settle_delay_seconds)
        return
    with perf_span(
        "acquire",
        "post_acquire_python_sleep",
        metadata={"status": status, "seconds": settle_delay_seconds},
    ):
        time.sleep(settle_delay_seconds)
