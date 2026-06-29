from __future__ import annotations

from typing import Any

MIN_MATCH_SCORE = 30
MIN_MUSICKIT_MATCH_SCORE = 60


def extract_artist_title(item: dict[str, Any]) -> tuple[str, str]:
    attributes = item.get("attributes")
    if isinstance(attributes, dict):
        return attributes.get("artistName", ""), attributes.get("name", "")
    return item.get("artistName", ""), item.get("trackName", "")


def score_track_match(wanted_artist: str, wanted_title: str, item: dict[str, Any]) -> int:
    artist, title = extract_artist_title(item)
    wanted_artist = wanted_artist.lower()
    wanted_title = wanted_title.lower()
    artist = artist.lower()
    title = title.lower()

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

    best_score = -1
    best: dict[str, Any] | None = None
    for item in results:
        score = score_track_match(wanted_artist, wanted_title, item)
        if score > best_score:
            best_score = score
            best = item

    if best is None or best_score < min_score:
        return None
    return best
