from __future__ import annotations

from collections.abc import Callable

from playlist_builder.canonical.enums import ImportStatus
from playlist_builder.canonical.models import CanonicalImportReport, CanonicalImportResult, CanonicalPlaylist
from playlist_builder.integration.youtube_music.auth import YouTubeMusicAuthPort
from playlist_builder.integration.youtube_music.client import build_youtube_music_client, wrap_client_error
from playlist_builder.integration.youtube_music.resolver import (
    YouTubeMusicResolutionOutcome,
    YouTubeMusicResolutionStatus,
)

DeliveryBatchCallback = Callable[[int, int], None]
_BATCH_SIZE = 50


class YouTubeMusicDelivery:
    """Materializes resolved tracks into a YouTube Music user playlist."""

    def __init__(self, auth: YouTubeMusicAuthPort) -> None:
        self._auth = auth
        self._playlist_ids_by_name: dict[str, str] = {}

    def _client(self):
        client = build_youtube_music_client(self._auth.headers_path())
        if client is None:
            raise ValueError(self._auth.unavailable_reason() or "Connexion YouTube Music requise.")
        return client

    def ensure_playlist(self, name: str) -> str:
        playlist_name = name.strip()
        if not playlist_name:
            raise ValueError("Le nom de playlist est requis.")
        cached = self._playlist_ids_by_name.get(playlist_name)
        if cached:
            return cached
        client = self._client()
        try:
            for item in client.list_library_playlists():
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title", "")).strip()
                playlist_id = str(item.get("playlistId") or "").strip()
                if title == playlist_name and playlist_id:
                    self._playlist_ids_by_name[playlist_name] = playlist_id
                    return playlist_id
            playlist_id = client.create_playlist(playlist_name)
        except Exception as exc:
            raise wrap_client_error(exc) from exc
        self._playlist_ids_by_name[playlist_name] = playlist_id
        return playlist_id

    def sync_playlist(
        self,
        playlist: CanonicalPlaylist,
        outcomes: list[YouTubeMusicResolutionOutcome],
        *,
        on_delivery_batch: DeliveryBatchCallback | None = None,
    ) -> CanonicalImportReport:
        playlist_id = self.ensure_playlist(playlist.name)
        resolved = [item for item in outcomes if item.status == YouTubeMusicResolutionStatus.RESOLVED and item.video_id]
        video_ids = [item.video_id for item in resolved]
        batches = [
            video_ids[index : index + _BATCH_SIZE]
            for index in range(0, len(video_ids), _BATCH_SIZE)
        ] or [[]]
        client = self._client()
        for batch_index, batch in enumerate(batches, start=1):
            if on_delivery_batch is not None:
                on_delivery_batch(batch_index, len(batches))
            if not batch:
                continue
            try:
                client.add_playlist_items(playlist_id, batch)
            except Exception as exc:
                raise wrap_client_error(exc) from exc

        results: list[CanonicalImportResult] = []
        for outcome in outcomes:
            results.append(_result_from_outcome(outcome, section_name="Playlist"))
        return CanonicalImportReport(
            playlist_name=playlist.name,
            results=tuple(results),
        )

    def add_resolved_track(
        self,
        playlist_name: str,
        outcome: YouTubeMusicResolutionOutcome,
        *,
        section_name: str,
        existing_keys: set[str] | None = None,
    ) -> CanonicalImportResult:
        known_keys = set(existing_keys or ())
        if outcome.status != YouTubeMusicResolutionStatus.RESOLVED or not outcome.video_id:
            return _result_from_outcome(outcome, section_name=section_name)
        track_key = outcome.track.identity_key
        if track_key in known_keys:
            return CanonicalImportResult(
                track=outcome.track,
                status=ImportStatus.SKIPPED,
                section_name=section_name,
            )
        playlist_id = self.ensure_playlist(playlist_name)
        client = self._client()
        try:
            client.add_playlist_items(playlist_id, [outcome.video_id])
        except Exception as exc:
            return CanonicalImportResult(
                track=outcome.track,
                status=ImportStatus.ERROR,
                section_name=section_name,
                error=str(wrap_client_error(exc)),
            )
        return CanonicalImportResult(
            track=outcome.track,
            status=ImportStatus.ADDED,
            section_name=section_name,
        )


def _result_from_outcome(outcome: YouTubeMusicResolutionOutcome, *, section_name: str) -> CanonicalImportResult:
    if outcome.status == YouTubeMusicResolutionStatus.RESOLVED:
        return CanonicalImportResult(
            track=outcome.track,
            status=ImportStatus.ADDED,
            section_name=section_name,
        )
    if outcome.status == YouTubeMusicResolutionStatus.NOT_FOUND:
        return CanonicalImportResult(
            track=outcome.track,
            status=ImportStatus.NOT_FOUND,
            section_name=section_name,
            error=outcome.error or "Introuvable sur YouTube Music",
        )
    return CanonicalImportResult(
        track=outcome.track,
        status=ImportStatus.ERROR,
        section_name=section_name,
        error=outcome.error or "Erreur YouTube Music",
    )
