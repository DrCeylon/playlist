from __future__ import annotations

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import (
    CanonicalAlbum,
    CanonicalArtist,
    CanonicalCandidate,
    CanonicalSearchRequest,
    CanonicalSearchResponse,
    CanonicalTrack,
)
from playlist_builder.core.models import CatalogMatch, TrackRef
from playlist_builder.discovery.models import DiscoveryCandidate, DiscoveryQuery
from playlist_builder.integration.apple_music.models import AppleITunesSearchHit, AppleMusicTrack
from playlist_builder.ui.shared.dto.autocomplete import ArtistSuggestion, TrackSuggestion
from playlist_builder.planning.models import CandidateTrack
from playlist_builder.scoring.match_engine import score_text_match
from playlist_builder.scoring.resolution import ResolutionCandidate


def canonical_candidate_from_itunes_hit(
    hit: AppleITunesSearchHit,
    *,
    source: str,
    reasons: tuple[str, ...] = (),
    request: CanonicalSearchRequest,
    wanted_artist: str,
    wanted_title: str,
) -> CanonicalCandidate:
    confidence = float(
        score_text_match(wanted_artist or request.query, wanted_title or request.query, hit.artist_name, hit.track_name)
    )
    hints: list[str] = []
    if hit.track_view_url:
        hints.append(hit.track_view_url)
    if hit.track_id:
        hints.append(f"itunes_track_id:{hit.track_id}")
    return CanonicalCandidate(
        track=CanonicalTrack(
            artist=CanonicalArtist(name=hit.artist_name),
            title=hit.track_name,
            album=CanonicalAlbum(title=hit.collection_name, artist=CanonicalArtist(name=hit.artist_name))
            if hit.collection_name
            else None,
            explicit=hit.is_explicit,
            genres=(hit.primary_genre_name,) if hit.primary_genre_name else (),
        ),
        source=source,
        provider_hints=tuple(hints),
        raw_confidence=confidence,
        reasons=reasons,
    )


def discovery_candidate_from_canonical(
    candidate: CanonicalCandidate,
    *,
    query: DiscoveryQuery,
    album: str = "",
    genre: str = "",
) -> DiscoveryCandidate:
    return DiscoveryCandidate(
        track=candidate.track,
        score=max(1.0, 40.0 * query.weight),
        source=candidate.source or ProviderId.APPLE_MUSIC.value,
        reasons=(*candidate.reasons, f"query:{query.source}:{query.term}"),
        album=candidate.track.album.title if candidate.track.album else album,
        genre=genre or (candidate.track.genres[0] if candidate.track.genres else ""),
        explicit=candidate.track.explicit,
        provider_id=ProviderId.APPLE_MUSIC,
        catalog_url=candidate.provider_hints[0] if candidate.provider_hints else "",
    )


def discovery_candidate_to_planning(candidate: DiscoveryCandidate) -> CandidateTrack:
    from playlist_builder.canonical.compat import legacy_track_from_canonical

    return CandidateTrack(
        track=legacy_track_from_canonical(
            candidate.track,
            section=candidate.section or "Discovery",
        ),
        score=candidate.score,
        source=candidate.source,
        reasons=candidate.reasons,
        album=candidate.album,
        genre=candidate.genre,
        mood=candidate.mood,
        language=candidate.language,
        energy=candidate.energy,
        explicit=candidate.explicit,
    )


def catalog_match_from_track_search(
    track: TrackRef,
    *,
    hit: AppleITunesSearchHit | None,
    error: str = "",
) -> CatalogMatch:
    if hit is None:
        return CatalogMatch(query=track, error=error)
    return CatalogMatch(
        query=track,
        matched_artist=hit.artist_name,
        matched_title=hit.track_name,
        url=hit.track_view_url,
        raw=hit.raw,
        error=error,
    )


def catalog_match_from_term_search(
    *,
    wanted_artist: str,
    wanted_title: str,
    term: str,
    hit: AppleITunesSearchHit | None,
    error: str = "",
) -> CatalogMatch:
    probe = TrackRef(artist=wanted_artist or term, title=wanted_title or term, section="Catalog")
    if hit is None:
        return CatalogMatch(query=probe, error=error)
    return CatalogMatch(
        query=probe,
        matched_artist=hit.artist_name,
        matched_title=hit.track_name,
        url=hit.track_view_url,
        raw=hit.raw,
        error=error,
    )


def search_response_from_hit(
    request: CanonicalSearchRequest,
    hit: AppleITunesSearchHit | None,
    *,
    source: str,
    reasons: tuple[str, ...] = (),
) -> CanonicalSearchResponse:
    if hit is None:
        return CanonicalSearchResponse(request=request, candidates=())
    candidate = canonical_candidate_from_itunes_hit(
        hit,
        source=source,
        reasons=reasons,
        request=request,
        wanted_artist=request.wanted_artist,
        wanted_title=request.wanted_title,
    )
    return CanonicalSearchResponse(request=request, candidates=(candidate,))


def apple_music_track_from_fields(
    *,
    persistent_id: str,
    artist: str,
    title: str,
    query: str = "",
) -> AppleMusicTrack | None:
    if not persistent_id.strip():
        return None
    return AppleMusicTrack(
        persistent_id=persistent_id.strip(),
        artist=artist.strip(),
        title=title.strip(),
        query=query.strip(),
    )


def resolution_candidates_from_apple_music_tracks(
    tracks: list[AppleMusicTrack],
) -> list[ResolutionCandidate]:
    return [
        ResolutionCandidate(
            artist=track.artist,
            title=track.title,
            provider_key=track.persistent_id,
            query=track.query,
        )
        for track in tracks
    ]


def _normalize_identity(value: str) -> str:
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


def _release_year_from_hit(hit: AppleITunesSearchHit) -> int | None:
    release_date = hit.release_date
    if not release_date:
        return None
    try:
        return int(release_date[:4])
    except ValueError:
        return None


def artist_suggestion_from_itunes_hit(hit: AppleITunesSearchHit) -> ArtistSuggestion:
    display_name = hit.artist_name.strip()
    artist_id = hit.artist_id or _normalize_identity(display_name)
    return ArtistSuggestion(
        id=artist_id,
        display_name=display_name,
        artwork_url=hit.artwork_url,
        artist_type=hit.kind or hit.wrapper_type,
    )


def track_suggestion_from_itunes_hit(hit: AppleITunesSearchHit) -> TrackSuggestion:
    title = hit.track_name.strip()
    artist_name = hit.artist_name.strip()
    track_id = hit.track_id or _normalize_identity(f"{artist_name}-{title}")
    return TrackSuggestion(
        id=track_id,
        title=title,
        artist_name=artist_name,
        album_title=hit.collection_name,
        release_year=_release_year_from_hit(hit),
        duration_ms=hit.track_time_millis,
        artwork_url=hit.artwork_url,
        primary_genre_name=hit.primary_genre_name,
    )


def canonical_candidate_from_apple_music_track(
    track: AppleMusicTrack,
    *,
    score: float,
) -> CanonicalCandidate:
    return CanonicalCandidate(
        track=CanonicalTrack(
            artist=CanonicalArtist(name=track.artist),
            title=track.title,
        ),
        source=ProviderId.APPLE_MUSIC.value,
        provider_hints=(track.persistent_id,),
        raw_confidence=score,
        reasons=(f"query:{track.query}",) if track.query else (),
    )
