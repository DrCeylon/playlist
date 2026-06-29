from __future__ import annotations

from typing import Any

MIN_MATCH_SCORE = 30


def score_track_match(wanted_artist: str, wanted_title: str, item: dict[str, Any]) -> int:
    artist = item.get("artistName", "").lower()
    title = item.get("trackName", "").lower()
    wanted_artist = wanted_artist.lower()
    wanted_title = wanted_title.lower()

    value = 0
    if wanted_artist == artist:
        value += 50
    elif wanted_artist in artist or artist in wanted_artist:
        value += 30
    if wanted_title == title:
        value += 50
    elif wanted_title in title or title in wanted_title:
        value += 30
    return value


def pick_best_match(
    wanted_artist: str,
    wanted_title: str,
    results: list[dict[str, Any]],
    *,
    min_score: int = MIN_MATCH_SCORE,
) -> dict[str, Any] | None:
    if not results:
        return None

    best = max(results, key=lambda item: score_track_match(wanted_artist, wanted_title, item))
    if score_track_match(wanted_artist, wanted_title, best) < min_score:
        return None
    return best
