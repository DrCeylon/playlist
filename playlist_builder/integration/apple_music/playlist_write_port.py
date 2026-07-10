from __future__ import annotations

from playlist_builder.canonical.identity import track_identity_key
from playlist_builder.core.models import TrackRef
from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient
from playlist_builder.integration.ports.playlist_write import ProviderPlaylistWritePort
from playlist_builder.ui.shared.dto.remote_playlist import RemotePlaylistTrack


class AppleMusicPlaylistWritePort(ProviderPlaylistWritePort):
    """Write user playlists in Music.app via AppleScript."""

    def __init__(self, applescript: AppleScriptClient) -> None:
        self._applescript = applescript

    def create_playlist(self, name: str) -> str:
        playlist_name = name.strip()
        if not playlist_name:
            raise ValueError("Le nom de playlist est requis.")
        self._applescript.ensure_running(activate=False)
        self._applescript.ensure_playlist(playlist_name)
        for playlist_id, listed_name, _ in self._applescript.list_user_playlists():
            if listed_name == playlist_name:
                return playlist_id
        raise ValueError(f"Playlist créée mais introuvable : {playlist_name}")

    def upsert_tracks(self, remote_playlist_id: str, tracks: tuple[RemotePlaylistTrack, ...]) -> None:
        if not tracks:
            return
        playlist_name = self._applescript.playlist_name_for_id(remote_playlist_id)
        self._applescript.ensure_running(activate=False)
        existing_keys = self._applescript.load_playlist_keys(playlist_name)
        tracks_to_add = [
            track
            for track in tracks
            if track_identity_key(track.artist, track.title) not in existing_keys
        ]
        if not tracks_to_add:
            return
        refs = [TrackRef(artist=track.artist, title=track.title, section="") for track in tracks_to_add]
        candidates = self._applescript.collect_candidates_batch(refs)
        persistent_ids: list[str | None] = []
        for index, candidate_list in enumerate(candidates):
            track = tracks_to_add[index]
            if not candidate_list:
                raise ValueError(f"Morceau introuvable dans la bibliothèque : {track.artist} — {track.title}")
            persistent_ids.append(candidate_list[0].persistent_id)
        statuses = self._applescript.add_tracks_by_persistent_id_batch(playlist_name, persistent_ids)
        for status in statuses:
            normalized = str(status).strip().lower()
            if normalized.startswith("error") or normalized == "not_found":
                raise ValueError(f"Échec d'ajout Apple Music : {status}")

    def remove_tracks(self, remote_playlist_id: str, remote_track_ids: tuple[str, ...]) -> None:
        playlist_name = self._applescript.playlist_name_for_id(remote_playlist_id)
        self._applescript.ensure_running(activate=False)
        self._applescript.remove_tracks_by_id(playlist_name, list(remote_track_ids))
