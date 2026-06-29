from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from playlist_builder.planning.models import CandidateTrack, GeneratedPlaylist


@dataclass(frozen=True)
class PlaylistAnalysis:
    track_count: int
    artist_count: int
    top_artists: tuple[tuple[str, int], ...]
    genres: tuple[tuple[str, int], ...]
    moods: tuple[tuple[str, int], ...]
    languages: tuple[tuple[str, int], ...]
    average_score: float
    average_energy: float | None

    @property
    def diversity_ratio(self) -> float:
        if self.track_count == 0:
            return 0.0
        return self.artist_count / self.track_count


class PlaylistAnalyzer:
    """Minimal analysis engine.

    This is the first version of the future "analyse this playlist" feature.
    It works on generated candidates now and can later be backed by Apple Music
    metadata, BPM, genres and listening history.
    """

    def analyze(self, playlist: GeneratedPlaylist) -> PlaylistAnalysis:
        return analyze_candidates(list(playlist.candidates))


def analyze_candidates(candidates: list[CandidateTrack]) -> PlaylistAnalysis:
    artists = Counter(candidate.track.artist for candidate in candidates if candidate.track.artist)
    genres = Counter(candidate.genre for candidate in candidates if candidate.genre)
    moods = Counter(candidate.mood for candidate in candidates if candidate.mood)
    languages = Counter(candidate.language for candidate in candidates if candidate.language)
    energies = [candidate.energy for candidate in candidates if candidate.energy is not None]

    average_score = sum(candidate.score for candidate in candidates) / len(candidates) if candidates else 0.0
    average_energy = sum(energies) / len(energies) if energies else None

    return PlaylistAnalysis(
        track_count=len(candidates),
        artist_count=len(artists),
        top_artists=tuple(artists.most_common(5)),
        genres=tuple(genres.most_common()),
        moods=tuple(moods.most_common()),
        languages=tuple(languages.most_common()),
        average_score=average_score,
        average_energy=average_energy,
    )
