from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from playlist_builder import __version__
from playlist_builder.canonical.constants import DEFAULT_PLAYLIST_DESCRIPTION
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.catalog.rate_limiter import RateLimiter
from playlist_builder.catalog.retry_policy import RetryPolicy
from playlist_builder.catalog.scoring import MIN_MUSICKIT_MATCH_SCORE, pick_best_match
from playlist_builder.core.models import TrackAddResult, TrackAddStatus, TrackRef

API_BASE = "https://api.music.apple.com/v1"
USER_AGENT = f"PlaylistBuilder/{__version__} (MusicKit; Python)"
TRACKS_CHUNK_SIZE = 100


class MusicKitConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MusicKitCredentials:
    developer_token: str
    user_token: str

    @classmethod
    def from_env(cls) -> MusicKitCredentials:
        developer_token = os.getenv("APPLE_MUSIC_DEVELOPER_TOKEN", "").strip()
        user_token = os.getenv("APPLE_MUSIC_USER_TOKEN", "").strip()
        if not developer_token or not user_token:
            raise MusicKitConfigurationError(
                "MusicKit nécessite APPLE_MUSIC_DEVELOPER_TOKEN et APPLE_MUSIC_USER_TOKEN."
            )
        return cls(developer_token=developer_token, user_token=user_token)


class MusicKitClient:
    """Apple Music API client.

    Supports create/update only. Playlist and track deletion are intentionally
    excluded from the product surface.
    """

    def __init__(
        self,
        credentials: MusicKitCredentials,
        storefront: str = "us",
        *,
        cache: JsonCache | None = None,
        rate_limiter: RateLimiter | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.credentials = credentials
        self.storefront = storefront
        self.cache = cache
        self.rate_limiter = rate_limiter or RateLimiter(minimum_interval_seconds=0.3)
        self.retry_policy = retry_policy or RetryPolicy()

    @classmethod
    def from_env(
        cls,
        storefront: str = "us",
        *,
        cache: JsonCache | None = None,
    ) -> MusicKitClient:
        return cls(MusicKitCredentials.from_env(), storefront=storefront, cache=cache)

    def create_or_update_playlist(
        self,
        name: str,
        tracks: list[TrackRef],
        *,
        description: str = DEFAULT_PLAYLIST_DESCRIPTION,
        allow_duplicates: bool = False,
    ) -> list[TrackAddResult]:
        playlist_id = self.find_library_playlist_id_by_name(name)
        existing_keys = (
            set()
            if allow_duplicates or playlist_id is None
            else self.load_library_playlist_keys(playlist_id)
        )

        results: list[TrackAddResult] = []
        song_ids_to_add: list[str] = []

        for track in tracks:
            if not allow_duplicates and track.key in existing_keys:
                results.append(TrackAddResult(track=track, status=TrackAddStatus.SKIPPED))
                continue

            song_id, error = self.find_song_id(track)
            if song_id:
                song_ids_to_add.append(song_id)
                if not allow_duplicates:
                    existing_keys.add(track.key)
                results.append(TrackAddResult(track=track, status=TrackAddStatus.ADDED))
            else:
                results.append(
                    TrackAddResult(track=track, status=TrackAddStatus.NOT_FOUND, error=error)
                )

        if playlist_id is None:
            playlist_id = self.create_library_playlist(name, description, song_ids_to_add)
        elif song_ids_to_add:
            self.add_tracks_to_library_playlist(playlist_id, song_ids_to_add)

        return results

    def find_song_id(self, track: TrackRef) -> tuple[str | None, str]:
        cache_key = f"musickit::{self.storefront}::{track.key}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                song_id = cached.get("song_id")
                return song_id, cached.get("error", "") if not song_id else ""

        term = f"{track.artist} {track.title}"
        query = urllib.parse.urlencode({"term": term, "types": "songs", "limit": "10"})
        data = self._request_json("GET", f"/catalog/{self.storefront}/search?{query}")
        candidates = data.get("results", {}).get("songs", {}).get("data", [])
        best = pick_best_match(
            track.artist,
            track.title,
            candidates,
            min_score=MIN_MUSICKIT_MATCH_SCORE,
        )

        if not best:
            payload = {"song_id": None, "error": "Aucune correspondance MusicKit fiable."}
            if self.cache:
                self.cache.set(cache_key, payload)
            return None, payload["error"]

        song_id = best.get("id")
        if self.cache:
            self.cache.set(cache_key, {"song_id": song_id, "error": ""})
        return song_id, ""

    def find_library_playlist_id_by_name(self, name: str) -> str | None:
        next_path: str | None = "/me/library/playlists?limit=100"
        while next_path:
            data = self._request_json("GET", next_path)
            for playlist in data.get("data", []):
                if playlist.get("attributes", {}).get("name") == name:
                    return playlist.get("id")
            next_path = data.get("next")
        return None

    def load_library_playlist_keys(self, playlist_id: str) -> set[str]:
        keys: set[str] = set()
        next_path: str | None = f"/me/library/playlists/{playlist_id}/tracks?limit=100"
        while next_path:
            data = self._request_json("GET", next_path)
            for track in data.get("data", []):
                attrs = track.get("attributes", {})
                artist = str(attrs.get("artistName", "")).strip().lower()
                title = str(attrs.get("name", "")).strip().lower()
                if artist and title:
                    keys.add(f"{artist}::{title}")
            next_path = data.get("next")
        return keys

    def create_library_playlist(self, name: str, description: str, song_ids: list[str]) -> str:
        payload: dict[str, Any] = {
            "attributes": {
                "name": name,
                "description": description,
            }
        }
        if song_ids:
            payload["relationships"] = {
                "tracks": {
                    "data": [{"id": song_id, "type": "songs"} for song_id in song_ids]
                }
            }
        data = self._request_json("POST", "/me/library/playlists", payload)
        playlist_id = data.get("data", [{}])[0].get("id") or data.get("id")
        if not playlist_id:
            raise RuntimeError("MusicKit n'a pas renvoyé l'identifiant de la playlist créée.")
        return playlist_id

    def add_tracks_to_library_playlist(self, playlist_id: str, song_ids: list[str]) -> None:
        for offset in range(0, len(song_ids), TRACKS_CHUNK_SIZE):
            chunk = song_ids[offset : offset + TRACKS_CHUNK_SIZE]
            payload = {"data": [{"id": song_id, "type": "songs"} for song_id in chunk]}
            self._request_json("POST", f"/me/library/playlists/{playlist_id}/tracks", payload)

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = path if path.startswith("http") else f"{API_BASE}{path}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        last_error = ""

        for attempt in range(1, self.retry_policy.max_attempts + 1):
            self.rate_limiter.wait()
            request = urllib.request.Request(url, data=body, method=method)
            request.add_header("Authorization", f"Bearer {self.credentials.developer_token}")
            request.add_header("Music-User-Token", self.credentials.user_token)
            request.add_header("Content-Type", "application/json")
            request.add_header("User-Agent", USER_AGENT)

            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last_error = f"MusicKit HTTP {exc.code}: {detail}"
                if exc.code != 429:
                    raise RuntimeError(last_error) from exc
            except Exception as exc:
                raise RuntimeError(str(exc)) from exc

            delay = self.retry_policy.delay_for_attempt(attempt)
            time.sleep(delay)

        raise RuntimeError(last_error or "MusicKit request failed after retries.")
