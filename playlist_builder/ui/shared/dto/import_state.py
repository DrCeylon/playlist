from __future__ import annotations

from dataclasses import dataclass

from playlist_builder.ui.shared.dto.enums import ImportPhase, ImportTrackStatus


@dataclass(frozen=True, slots=True)
class ImportTrackOutcome:
    artist: str
    title: str
    section: str
    status: ImportTrackStatus
    message: str = ""


@dataclass(frozen=True, slots=True)
class ImportProgressState:
    phase: ImportPhase
    playlist_name: str
    total_tracks: int = 0
    processed_tracks: int = 0
    added_count: int = 0
    skipped_count: int = 0
    not_found_count: int = 0
    error_count: int = 0
    cache_hit_count: int = 0
    acquisition_count: int = 0
    current_track_label: str = ""

    @property
    def progress_ratio(self) -> float:
        if self.total_tracks <= 0:
            return 0.0
        return min(1.0, self.processed_tracks / self.total_tracks)


@dataclass(frozen=True, slots=True)
class ImportResultState:
    playlist_name: str
    outcomes: tuple[ImportTrackOutcome, ...] = ()
    phase: ImportPhase = ImportPhase.COMPLETED
    import_session_id: str = ""
    manual_token: str = ""
    manual_artist: str = ""
    manual_title: str = ""
    manual_instructions: str = ""
    manual_catalog_label: str = ""
    manual_catalog_url: str = ""
    manual_album: str = ""

    @property
    def added_count(self) -> int:
        return sum(1 for item in self.outcomes if item.status == ImportTrackStatus.ADDED)

    @property
    def not_found_count(self) -> int:
        return sum(1 for item in self.outcomes if item.status == ImportTrackStatus.NOT_FOUND)
