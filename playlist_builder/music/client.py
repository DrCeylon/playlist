from __future__ import annotations

from pathlib import Path

from playlist_builder.canonical.compat import canonical_track_from_legacy
from playlist_builder.canonical.enums import ImportStatus
from playlist_builder.canonical.models import CanonicalPlaylist, CanonicalPlaylistSection
from playlist_builder.core.models import TrackAddResult, TrackAddStatus, TrackRef
from playlist_builder.integration.apple_music.gateway import build_apple_music_import_service
from playlist_builder.integration.apple_music.import_service import AppleMusicImportService
from playlist_builder.integration.apple_music.resolver import AppleMusicResolutionStatus
from playlist_builder.integration.compat import track_results_aligned_with_playlist

BATCH_SIZE = 25
DEFAULT_IDENTITY_CACHE = Path("cache/apple_music_identity.json")


class MusicClient:
    """Backward-compatible facade over the Apple Music import service."""

    def __init__(
        self,
        *,
        import_service: AppleMusicImportService | None = None,
        identity_cache_path: Path | None = None,
    ) -> None:
        self._service = import_service or build_apple_music_import_service(
            identity_cache_path=identity_cache_path or DEFAULT_IDENTITY_CACHE,
        )

    @property
    def _applescript(self):
        return self._service.applescript

    def ensure_running(self) -> None:
        self._applescript.ensure_running()

    def ensure_playlist(self, name: str) -> None:
        self._applescript.ensure_playlist(name)

    def clear_playlist_tracks(self, playlist_name: str) -> None:
        self._applescript.clear_playlist_tracks(playlist_name)

    def load_playlist_keys(self, playlist_name: str) -> set[str]:
        return self._applescript.load_playlist_keys(playlist_name)

    def sync_playlist_order(
        self,
        playlist_name: str,
        tracks: list[TrackRef],
    ) -> list[TrackAddResult]:
        playlist = _playlist_from_tracks(playlist_name, tracks)
        report = self._service.import_playlist(playlist, sync=True)
        return _results_for_tracks(tracks, report)

    def add_tracks(
        self,
        playlist_name: str,
        tracks: list[TrackRef],
        *,
        existing_keys: set[str] | None = None,
        allow_duplicates: bool = False,
    ) -> list[TrackAddResult]:
        if not tracks:
            return []

        known_keys = existing_keys if existing_keys is not None else set()
        results: list[TrackAddResult | None] = [None] * len(tracks)
        pending: list[tuple[int, TrackRef]] = []

        for index, track in enumerate(tracks):
            if not allow_duplicates and track.key in known_keys:
                results[index] = TrackAddResult(track=track, status=TrackAddStatus.SKIPPED)
                continue
            pending.append((index, track))

        for offset in range(0, len(pending), BATCH_SIZE):
            batch = pending[offset : offset + BATCH_SIZE]
            indices, batch_tracks = zip(*batch, strict=True)
            batch_results = self._add_tracks_batch(playlist_name, list(batch_tracks))
            for index, result in zip(indices, batch_results, strict=True):
                if result.status == TrackAddStatus.ADDED:
                    known_keys.add(result.track.key)
                results[index] = result

        return [result for result in results if result is not None]

    def _add_tracks_batch(self, playlist_name: str, tracks: list[TrackRef]) -> list[TrackAddResult]:
        rows = [(canonical_track_from_legacy(track), track.section) for track in tracks]
        outcomes = self._service.resolver.resolve_batch(rows)

        persistent_ids: list[str | None] = []
        for outcome in outcomes:
            if outcome.status == AppleMusicResolutionStatus.RESOLVED:
                persistent_ids.append(outcome.persistent_id)
            else:
                persistent_ids.append(None)

        delivery_statuses = self._applescript.add_tracks_by_persistent_id_batch(
            playlist_name,
            persistent_ids,
        )

        batch_results: list[TrackAddResult] = []
        for track, outcome, delivery_status in zip(tracks, outcomes, delivery_statuses, strict=True):
            if outcome.status == AppleMusicResolutionStatus.ERROR:
                batch_results.append(
                    TrackAddResult(track=track, status=TrackAddStatus.ERROR, error=outcome.error)
                )
                continue
            if outcome.status == AppleMusicResolutionStatus.NOT_FOUND:
                batch_results.append(TrackAddResult(track=track, status=TrackAddStatus.NOT_FOUND))
                continue
            if delivery_status.startswith("added"):
                batch_results.append(TrackAddResult(track=track, status=TrackAddStatus.ADDED))
            elif delivery_status.startswith("not_found"):
                batch_results.append(TrackAddResult(track=track, status=TrackAddStatus.NOT_FOUND))
            else:
                batch_results.append(
                    TrackAddResult(
                        track=track,
                        status=TrackAddStatus.ERROR,
                        error="Erreur AppleScript lors de l'ajout.",
                    )
                )
        return batch_results

    @staticmethod
    def _normalize_key(value: str) -> str:
        from playlist_builder.canonical.identity import track_identity_key

        artist, _, title = value.partition("::")
        return track_identity_key(artist, title)


def _playlist_from_tracks(name: str, tracks: list[TrackRef]) -> CanonicalPlaylist:
    section_order: list[str] = []
    section_tracks: dict[str, list] = {}
    for track in tracks:
        if track.section not in section_tracks:
            section_order.append(track.section)
            section_tracks[track.section] = []
        section_tracks[track.section].append(canonical_track_from_legacy(track))

    return CanonicalPlaylist(
        name=name,
        sections=tuple(
            CanonicalPlaylistSection(name=section_name, tracks=tuple(section_tracks[section_name]))
            for section_name in section_order
        ),
    )


def _results_for_tracks(tracks: list[TrackRef], report) -> list[TrackAddResult]:
    from playlist_builder.integration.compat import track_results_aligned_with_playlist

    return track_results_aligned_with_playlist(tracks, report)
