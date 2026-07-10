from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.integration.youtube_music.secrets import sanitize_user_message
from playlist_builder.ui.shared.dto.remote_playlist import (
    RemotePlaylist,
    RemotePlaylistSnapshot,
    RemotePlaylistTrack,
    remote_playlist_snapshot_checksum,
    utc_now_iso,
)


def _artist_name(artists: Any) -> str:
    if not isinstance(artists, list) or not artists:
        return ""
    first = artists[0]
    if isinstance(first, dict):
        return str(first.get("name", "")).strip()
    return str(first).strip()


def map_library_playlist(item: dict[str, Any], *, snapshot_at_iso: str) -> RemotePlaylist:
    playlist_id = str(item.get("playlistId") or item.get("browseId") or "").strip()
    name = str(item.get("title", "")).strip() or playlist_id
    count_raw = item.get("count")
    track_count = int(count_raw) if isinstance(count_raw, int) else 0
    return RemotePlaylist(
        provider_id=ProviderId.YOUTUBE_MUSIC,
        remote_playlist_id=playlist_id,
        name=name,
        track_count=track_count,
        is_public=False,
        owner_label="YouTube Music",
        snapshot_at_iso=snapshot_at_iso,
    )


def map_playlist_snapshot(
    payload: dict[str, Any],
    *,
    remote_playlist_id: str,
    source_kind: str,
    source_url: str = "",
) -> RemotePlaylistSnapshot:
    title = str(payload.get("title") or payload.get("name") or remote_playlist_id).strip()
    tracks_raw = payload.get("tracks") or payload.get("contents") or []
    tracks: list[RemotePlaylistTrack] = []
    if isinstance(tracks_raw, list):
        for index, item in enumerate(tracks_raw, start=1):
            if not isinstance(item, dict):
                continue
            video_id = str(item.get("videoId") or item.get("setVideoId") or item.get("id") or "").strip()
            artist = _artist_name(item.get("artists"))
            track_title = str(item.get("title", "")).strip()
            album = ""
            album_obj = item.get("album")
            if isinstance(album_obj, dict):
                album = str(album_obj.get("name", "")).strip()
            duration_seconds = item.get("duration_seconds")
            duration_ms = int(duration_seconds) * 1000 if isinstance(duration_seconds, (int, float)) else 0
            tracks.append(
                RemotePlaylistTrack(
                    remote_track_id=video_id or f"yt-track-{index}",
                    artist=artist,
                    title=track_title,
                    album=album,
                    duration_ms=duration_ms,
                    position=index,
                )
            )
    track_tuple = tuple(tracks)
    snapshot_at = utc_now_iso()
    return RemotePlaylistSnapshot(
        provider_id=ProviderId.YOUTUBE_MUSIC,
        remote_playlist_id=remote_playlist_id,
        name=title,
        snapshot_at_iso=snapshot_at,
        tracks=track_tuple,
        track_count=len(track_tuple),
        checksum=remote_playlist_snapshot_checksum(track_tuple),
        source_kind=source_kind,
        source_url=source_url,
    )


class YouTubeMusicAuthConfigStore:
    """Persist only a local path reference — never auth header contents."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    def load(self) -> dict[str, str]:
        if not self._config_path.exists():
            return {}
        try:
            payload = json.loads(self._config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        return {str(key): str(value) for key, value in payload.items() if isinstance(key, str) and isinstance(value, str)}

    def save(self, payload: dict[str, str]) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def clear(self) -> None:
        if self._config_path.exists():
            self._config_path.unlink()

    def headers_path(self) -> Path | None:
        raw = self.load().get("headers_file_path", "").strip()
        if not raw:
            return None
        return Path(raw).expanduser()


def safe_provider_error(exc: Exception) -> str:
    return sanitize_user_message(str(exc) or "Erreur YouTube Music expérimentale.")
