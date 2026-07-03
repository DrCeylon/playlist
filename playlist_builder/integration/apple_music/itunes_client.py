from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from playlist_builder import __version__
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.catalog.rate_limiter import RateLimiter
from playlist_builder.catalog.retry_policy import RetryPolicy
from playlist_builder.core.models import TrackRef
from playlist_builder.infrastructure.cache.keys import catalog_entry_key
from playlist_builder.infrastructure.cache.store import JsonCache
from playlist_builder.integration.apple_music.models import AppleITunesSearchHit
from playlist_builder.scoring.match_engine import artist_name_matches, pick_best_match

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
USER_AGENT = f"PlaylistBuilder/{__version__} (AppleMusicCatalog; Python)"
_PROVIDER_ID = ProviderId.APPLE_MUSIC


class ITunesSearchClient:
    """Low-level iTunes Search API client with namespaced cache keys."""

    def __init__(
        self,
        country: str = "us",
        *,
        cache: JsonCache | None = None,
        rate_limiter: RateLimiter | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.country = country
        self.cache = cache
        self.rate_limiter = rate_limiter or RateLimiter(minimum_interval_seconds=0.5)
        self.retry_policy = retry_policy or RetryPolicy()

    def search_track(self, track: TrackRef, *, limit: int = 5) -> tuple[AppleITunesSearchHit | None, str]:
        new_key = catalog_entry_key(_PROVIDER_ID, "track", f"{self.country}::{track.key}")
        legacy_key = f"itunes::{self.country}::{track.key}"
        cached = self._read_cache(new_key, legacy_key)
        if cached is not None:
            return self._hit_from_cache_payload(cached)

        total_wait = 0.0
        last_error = ""
        term = f"{track.artist} {track.title}".strip()

        for attempt in range(1, self.retry_policy.max_attempts + 1):
            self.rate_limiter.wait()
            try:
                hit = self._search_once(
                    term,
                    limit=limit,
                    wanted_artist=track.artist,
                    wanted_title=track.title,
                )
                self._write_cache(new_key, self._serialize_hit(hit))
                return hit, ""
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

        self._write_cache(new_key, self._serialize_hit(None, error=last_error))
        return None, last_error

    def search_term(
        self,
        term: str,
        *,
        wanted_artist: str = "",
        wanted_title: str = "",
        limit: int = 5,
    ) -> tuple[AppleITunesSearchHit | None, str]:
        normalized = term.strip().lower()
        new_key = catalog_entry_key(_PROVIDER_ID, "term", f"{self.country}::{normalized}::{limit}")
        legacy_key = f"itunes::term::{self.country}::{normalized}::{limit}"

        cached = self._read_cache(new_key, legacy_key)
        if cached is not None:
            return self._hit_from_cache_payload(cached)

        total_wait = 0.0
        last_error = ""

        for attempt in range(1, self.retry_policy.max_attempts + 1):
            self.rate_limiter.wait()
            try:
                hit = self._search_once(
                    term,
                    limit=limit,
                    wanted_artist=wanted_artist,
                    wanted_title=wanted_title,
                )
                self._write_cache(
                    new_key,
                    self._serialize_hit(hit),
                )
                return hit, ""
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
                f"⏳ Rate limit pour {term}. "
                f"Retry {attempt}/{self.retry_policy.max_attempts} dans {delay:.1f}s..."
            )
            time.sleep(delay)

        self._write_cache(new_key, self._serialize_hit(None, error=last_error))
        return None, last_error

    def search_artists(self, term: str, *, limit: int = 10) -> tuple[list[AppleITunesSearchHit], str]:
        normalized = term.strip().lower()
        new_key = catalog_entry_key(_PROVIDER_ID, "artist", f"{self.country}::{normalized}::{limit}")
        cached = self._read_cache(new_key, None)
        if cached is not None:
            return self._hits_from_cache_payload(cached)

        total_wait = 0.0
        last_error = ""
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            self.rate_limiter.wait()
            try:
                hits = self._search_entity(term, entity="musicArtist", limit=limit)
                self._write_cache(new_key, self._serialize_hits(hits))
                return hits, ""
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
            time.sleep(delay)

        self._write_cache(new_key, self._serialize_hits([], error=last_error))
        return [], last_error

    def search_tracks(
        self,
        term: str,
        *,
        limit: int = 10,
        wanted_artist: str = "",
    ) -> tuple[list[AppleITunesSearchHit], str]:
        normalized = term.strip().lower()
        artist_key = wanted_artist.strip().lower()
        new_key = catalog_entry_key(
            _PROVIDER_ID,
            "tracks",
            f"{self.country}::{normalized}::{artist_key}::{limit}",
        )
        cached = self._read_cache(new_key, None)
        if cached is not None:
            return self._hits_from_cache_payload(cached)

        search_term = term
        fetch_limit = limit
        if artist_key:
            search_term = f"{wanted_artist.strip()} {term}".strip()
            fetch_limit = max(limit * 5, 25)

        total_wait = 0.0
        last_error = ""
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            self.rate_limiter.wait()
            try:
                hits = self._search_entity(search_term, entity="song", limit=fetch_limit)
                if artist_key:
                    hits = [hit for hit in hits if artist_name_matches(wanted_artist, hit.artist_name)]
                hits = hits[:limit]
                self._write_cache(new_key, self._serialize_hits(hits))
                return hits, ""
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
            time.sleep(delay)

        self._write_cache(new_key, self._serialize_hits([], error=last_error))
        return [], last_error

    def _search_entity(self, term: str, *, entity: str, limit: int) -> list[AppleITunesSearchHit]:
        query = urllib.parse.urlencode(
            {
                "term": term,
                "country": self.country,
                "media": "music",
                "entity": entity,
                "limit": str(limit),
            }
        )
        url = f"{ITUNES_SEARCH_URL}?{query}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("results", [])
        hits: list[AppleITunesSearchHit] = []
        for item in results:
            if isinstance(item, dict):
                hits.append(AppleITunesSearchHit(item))
        return hits[:limit]

    def _search_once(
        self,
        term: str,
        *,
        limit: int,
        wanted_artist: str,
        wanted_title: str,
    ) -> AppleITunesSearchHit | None:
        query = urllib.parse.urlencode(
            {
                "term": term,
                "country": self.country,
                "media": "music",
                "entity": "song",
                "limit": str(limit),
            }
        )
        url = f"{ITUNES_SEARCH_URL}?{query}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("results", [])
        best = pick_best_match(wanted_artist or term, wanted_title or term, results)
        if best is None:
            return None
        return AppleITunesSearchHit(best)

    def _read_cache(self, new_key: str, legacy_key: str | None = None) -> dict[str, Any] | None:
        if self.cache is None:
            return None
        payload = self.cache.get(new_key)
        if payload is None and legacy_key:
            payload = self.cache.get(legacy_key)
        if isinstance(payload, dict):
            return payload
        return None

    def _write_cache(self, key: str, payload: dict[str, Any]) -> None:
        if self.cache is not None:
            self.cache.set(key, payload)

    @staticmethod
    def _serialize_hits(hits: list[AppleITunesSearchHit], *, error: str = "") -> dict[str, Any]:
        return {
            "hits": [hit.raw for hit in hits],
            "error": error,
        }

    @staticmethod
    def _hits_from_cache_payload(payload: dict[str, Any]) -> tuple[list[AppleITunesSearchHit], str]:
        error = str(payload.get("error", ""))
        raw_hits = payload.get("hits")
        if not isinstance(raw_hits, list):
            return [], error
        hits = [AppleITunesSearchHit(item) for item in raw_hits if isinstance(item, dict)]
        return hits, error

    @staticmethod
    def _serialize_hit(hit: AppleITunesSearchHit | None, *, error: str = "") -> dict[str, Any]:
        if hit is None:
            return {
                "matched_artist": "",
                "matched_title": "",
                "url": "",
                "raw": None,
                "error": error,
            }
        return {
            "matched_artist": hit.artist_name,
            "matched_title": hit.track_name,
            "url": hit.track_view_url,
            "raw": hit.raw,
            "error": error,
        }

    @staticmethod
    def _hit_from_cache_payload(payload: dict[str, Any]) -> tuple[AppleITunesSearchHit | None, str]:
        raw = payload.get("raw")
        error = str(payload.get("error", ""))
        if not isinstance(raw, dict):
            return None, error
        return AppleITunesSearchHit(raw), error
