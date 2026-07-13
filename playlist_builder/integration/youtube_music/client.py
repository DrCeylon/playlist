from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from playlist_builder.integration.youtube_music.experimental_guard import is_ytmusicapi_installed
from playlist_builder.integration.youtube_music.secrets import sanitize_user_message


@runtime_checkable
class YouTubeMusicClient(Protocol):
  def list_library_playlists(self) -> list[dict[str, Any]]: ...

  def get_playlist(self, playlist_id: str, *, limit: int | None = None) -> dict[str, Any]: ...

  def search_songs(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]: ...

  def create_playlist(self, title: str, *, description: str = "") -> str: ...

  def add_playlist_items(self, playlist_id: str, video_ids: list[str]) -> None: ...

  def remove_playlist_items(self, playlist_id: str, video_ids: list[str]) -> None: ...


class _YtmusicapiClient:
    def __init__(self, api: Any) -> None:
        self._api = api

    def list_library_playlists(self) -> list[dict[str, Any]]:
        playlists = self._api.get_library_playlists(limit=None) or []
        return list(playlists)

    def get_playlist(self, playlist_id: str, *, limit: int | None = None) -> dict[str, Any]:
        return self._api.get_playlist(playlist_id, limit=limit)

    def search_songs(self, query: str, *, limit: int = 10) -> list[dict[str, Any]]:
        results = self._api.search(query, filter="songs", limit=limit) or []
        return list(results)

    def create_playlist(self, title: str, *, description: str = "") -> str:
        playlist_id = self._api.create_playlist(title, description or "", privacy_status="PRIVATE")
        if not isinstance(playlist_id, str) or not playlist_id.strip():
            raise ValueError("Impossible de créer la playlist YouTube Music.")
        return playlist_id.strip()

    def add_playlist_items(self, playlist_id: str, video_ids: list[str]) -> None:
        if not video_ids:
            return
        self._api.add_playlist_items(playlist_id, video_ids)

    def remove_playlist_items(self, playlist_id: str, video_ids: list[str]) -> None:
        if not video_ids:
            return
        self._api.remove_playlist_items(playlist_id, [{"videoId": video_id} for video_id in video_ids])


def load_headers_file(path: Path) -> dict[str, str]:
    if not path.exists() or not path.is_file():
        raise ValueError("Le fichier d'authentification est introuvable.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Le fichier d'authentification n'est pas un JSON valide.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Le fichier d'authentification doit contenir un objet JSON.")
    headers: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not isinstance(value, str):
            continue
        headers[key] = value
    if not headers:
        raise ValueError("Le fichier d'authentification ne contient aucun en-tête utilisable.")
    return headers


def build_youtube_music_client(headers_path: Path | None) -> YouTubeMusicClient | None:
    if not is_ytmusicapi_installed():
        return None
    from ytmusicapi import YTMusic

    if headers_path is not None:
        headers = load_headers_file(headers_path)
        return _YtmusicapiClient(YTMusic(headers))

    # Public reads may work without auth for some playlists; library calls will fail gracefully.
    return _YtmusicapiClient(YTMusic())


def wrap_client_error(exc: Exception) -> ValueError:
    return ValueError(sanitize_user_message(str(exc) or "Erreur YouTube Music expérimentale."))
