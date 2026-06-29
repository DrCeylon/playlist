from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from playlist_builder import __version__
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.catalog.rate_limiter import RateLimiter
from playlist_builder.catalog.retry_policy import RetryPolicy
from playlist_builder.catalog.scoring import pick_best_match
from playlist_builder.core.models import CatalogMatch, TrackRef

USER_AGENT = f"PlaylistBuilder/{__version__} (macOS; Python)"


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
        self.rate_limiter = rate_limiter or RateLimiter(minimum_interval_seconds=0.5)
        self.retry_policy = retry_policy or RetryPolicy()

    def search_track(self, track: TrackRef, limit: int = 5) -> CatalogMatch:
        cache_key = f"itunes::{self.country}::{track.key}"
        cached = self.cache.get(cache_key) if self.cache else None
        if cached is not None:
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
            print(
                f"⏳ Rate limit pour {track.label}. "
                f"Retry {attempt}/{self.retry_policy.max_attempts} dans {delay:.1f}s..."
            )
            time.sleep(delay)

        match = CatalogMatch(query=track, error=last_error)
        if self.cache:
            self.cache.set(
                cache_key,
                {
                    "matched_artist": "",
                    "matched_title": "",
                    "url": "",
                    "raw": None,
                    "error": last_error,
                },
            )
        return match

    def search_term(
        self,
        term: str,
        *,
        wanted_artist: str = "",
        wanted_title: str = "",
        limit: int = 5,
    ) -> CatalogMatch:
        normalized = term.strip().lower()
        cache_key = f"itunes::term::{self.country}::{normalized}::{limit}"
        cached = self.cache.get(cache_key) if self.cache else None
        if cached is not None:
            probe = TrackRef(artist=wanted_artist or term, title=wanted_title or term, section="Catalog")
            return CatalogMatch(query=probe, **cached)

        self.rate_limiter.wait()
        match = self._search_with_term(term, limit=limit, wanted_artist=wanted_artist, wanted_title=wanted_title)
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

    def _search_once(self, track: TrackRef, limit: int) -> CatalogMatch:
        return self._search_with_term(
            f"{track.artist} {track.title}".strip(),
            limit=limit,
            wanted_artist=track.artist,
            wanted_title=track.title,
        )

    def _search_with_term(
        self,
        term: str,
        *,
        limit: int,
        wanted_artist: str,
        wanted_title: str,
    ) -> CatalogMatch:
        query = urllib.parse.urlencode(
            {
                "term": term,
                "country": self.country,
                "media": "music",
                "entity": "song",
                "limit": str(limit),
            }
        )
        url = f"https://itunes.apple.com/search?{query}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("results", [])
        probe = TrackRef(artist=wanted_artist or term, title=wanted_title or term, section="Catalog")
        best = pick_best_match(wanted_artist or term, wanted_title or term, results)
        if best is None:
            return CatalogMatch(query=probe)

        return CatalogMatch(
            query=probe,
            matched_artist=best.get("artistName", ""),
            matched_title=best.get("trackName", ""),
            url=best.get("trackViewUrl", ""),
            raw=best,
        )
