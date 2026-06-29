from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict

from playlist_builder.catalog.cache import JsonCache
from playlist_builder.catalog.rate_limiter import RateLimiter
from playlist_builder.catalog.retry_policy import RetryPolicy
from playlist_builder.core.models import CatalogMatch, TrackRef


class AppleCatalogSearch:
    def __init__(
        self,
        country: str = "us",
        cache: JsonCache | None = None,
        rate_limiter: RateLimiter | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.country = country
        self.cache = cache
        self.rate_limiter = rate_limiter or RateLimiter()
        self.retry_policy = retry_policy or RetryPolicy()

    def search_track(self, track: TrackRef, limit: int = 5) -> CatalogMatch:
        cache_key = f"itunes::{self.country}::{track.key}"
        cached = self.cache.get(cache_key) if self.cache else None
        if cached:
            return CatalogMatch(query=track, **cached)

        total_wait = 0.0
        last_error = ""

        for attempt in range(1, self.retry_policy.max_attempts + 1):
            self.rate_limiter.wait()
            try:
                match = self._search_once(track, limit=limit)
                payload = {
                    "matched_artist": match.matched_artist,
                    "matched_title": match.matched_title,
                    "url": match.url,
                    "raw": match.raw,
                    "error": match.error,
                }
                if self.cache:
                    self.cache.set(cache_key, payload)
                return match
            except urllib.error.HTTPError as exc:
                last_error = f"HTTP Error {exc.code}: {exc.reason}"
                if exc.code != 429:
                    break
            except Exception as exc:
                last_error = str(exc)
                break

            delay = self.retry_policy.delay_for_attempt(attempt)
            if total_wait + delay > self.retry_policy.max_total_wait:
                break
            total_wait += delay
            print(f"⏳ Rate limit pour {track.label}. Retry {attempt}/{self.retry_policy.max_attempts} dans {delay:.1f}s...")
            time.sleep(delay)

        match = CatalogMatch(query=track, error=last_error)
        if self.cache:
            self.cache.set(cache_key, {
                "matched_artist": "",
                "matched_title": "",
                "url": "",
                "raw": None,
                "error": last_error,
            })
        return match

    def _search_once(self, track: TrackRef, limit: int) -> CatalogMatch:
        query = urllib.parse.urlencode({
            "term": f"{track.artist} {track.title}",
            "country": self.country,
            "media": "music",
            "entity": "song",
            "limit": str(limit),
        })
        url = f"https://itunes.apple.com/search?{query}"
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("results", [])
        if not results:
            return CatalogMatch(query=track)

        best = sorted(results, key=lambda item: self._score(track, item), reverse=True)[0]
        return CatalogMatch(
            query=track,
            matched_artist=best.get("artistName", ""),
            matched_title=best.get("trackName", ""),
            url=best.get("trackViewUrl", ""),
            raw=best,
        )

    @staticmethod
    def _score(track: TrackRef, item: dict) -> int:
        wanted_artist = track.artist.lower()
        wanted_title = track.title.lower()
        artist = item.get("artistName", "").lower()
        title = item.get("trackName", "").lower()
        score = 0
        if wanted_artist == artist:
            score += 50
        elif wanted_artist in artist or artist in wanted_artist:
            score += 30
        if wanted_title == title:
            score += 50
        elif wanted_title in title or title in wanted_title:
            score += 30
        return score
