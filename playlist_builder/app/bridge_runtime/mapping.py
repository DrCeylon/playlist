from __future__ import annotations

from playlist_builder.canonical.enums import ConfidenceLevel, ProviderId
from playlist_builder.core.models import TrackAddResult, TrackAddStatus, TrackRef
from playlist_builder.planning.models import (
    ConstraintKind,
    EnergyProfile,
    ExclusionRule as PlanningExclusionRule,
    GeneratedPlaylist,
    GenerationConstraints,
    InclusionRule,
    PlaylistRequest,
    SeedTrack,
)
from playlist_builder.ui.shared.dto.enums import EnergyCurveProfile, ExclusionKind, ImportPhase, ImportTrackStatus
from playlist_builder.ui.shared.dto.generation import (
    GeneratedSectionPreview,
    GeneratedTrackPreview,
    PlaylistGenerationRequest,
    PlaylistGenerationResult,
    SeedReference,
)
from playlist_builder.ui.shared.dto.import_state import ImportResultState, ImportTrackOutcome

_ENERGY_PROFILE_MAP: dict[EnergyCurveProfile, EnergyProfile] = {
    EnergyCurveProfile.CHILL: EnergyProfile.CHILL,
    EnergyCurveProfile.STEADY: EnergyProfile.STEADY,
    EnergyCurveProfile.RISING: EnergyProfile.RISING,
    EnergyCurveProfile.PARTY: EnergyProfile.PARTY,
    EnergyCurveProfile.MAX_FROM_START: EnergyProfile.MAX_FROM_START,
    EnergyCurveProfile.RANDOM: EnergyProfile.RANDOM,
}

_EXCLUSION_KIND_MAP: dict[ExclusionKind, ConstraintKind] = {
    ExclusionKind.ARTIST: ConstraintKind.ARTIST,
    ExclusionKind.ALBUM: ConstraintKind.ALBUM,
    ExclusionKind.TRACK: ConstraintKind.TRACK,
    ExclusionKind.GENRE: ConstraintKind.GENRE,
    ExclusionKind.MOOD: ConstraintKind.MOOD,
    ExclusionKind.LANGUAGE: ConstraintKind.LANGUAGE,
}

_SECTION_LABELS: dict[EnergyProfile, str] = {
    EnergyProfile.CHILL: "Cool-down",
    EnergyProfile.STEADY: "Plateau",
    EnergyProfile.RISING: "Montée",
    EnergyProfile.PARTY: "Peak",
    EnergyProfile.MAX_FROM_START: "Max dès le départ",
    EnergyProfile.RANDOM: "Surprise",
}


def ui_request_to_playlist_request(request: PlaylistGenerationRequest) -> PlaylistRequest:
    seeds = _build_seeds(request.seeds, request.keywords)
    exclusions = tuple(
        PlanningExclusionRule(
            kind=_EXCLUSION_KIND_MAP[rule.kind],
            value=rule.value,
            reason=rule.reason,
        )
        for rule in request.exclusions
    )
    inclusions = tuple(
        InclusionRule(kind=ConstraintKind.TERM, value=keyword, weight=1.0)
        for keyword in request.keywords
        if keyword.strip()
    )
    energy_profile = _ENERGY_PROFILE_MAP[request.energy_curve.profile]

    return PlaylistRequest(
        name=request.name.strip(),
        seeds=seeds,
        constraints=GenerationConstraints(
            target_track_count=request.target_track_count,
            target_duration_minutes=request.target_duration_minutes,
            energy_profile=energy_profile,
            preferred_terms=request.keywords,
            exclusions=exclusions,
            inclusions=inclusions,
        ),
        description=request.description.strip() or "Playlist générée par Resonance.",
    )


def generated_playlist_to_ui_result(
    generated: GeneratedPlaylist,
    *,
    provider_id: ProviderId,
) -> PlaylistGenerationResult:
    section_name = _SECTION_LABELS.get(
        generated.request.constraints.energy_profile,
        "Playlist",
    )
    tracks = tuple(
        GeneratedTrackPreview(
            artist=candidate.track.artist,
            title=candidate.track.title,
            section=candidate.track.section or section_name,
            score=round(candidate.score / 100.0, 4),
            confidence=_score_to_confidence(candidate.score),
            source=candidate.source,
        )
        for candidate in generated.candidates
    )
    average = round(sum(track.score for track in tracks) / len(tracks), 4) if tracks else 0.0
    return PlaylistGenerationResult(
        playlist_name=generated.request.name,
        sections=(GeneratedSectionPreview(name=section_name, tracks=tracks),),
        average_score=average,
        provider_id=provider_id,
    )


def generation_result_to_playlist_definition(result: PlaylistGenerationResult):
    from playlist_builder.core.models import PlaylistDefinition, PlaylistSection

    sections = []
    for section in result.sections:
        tracks = tuple(
            TrackRef(artist=track.artist, title=track.title, section=section.name)
            for track in section.tracks
        )
        sections.append(PlaylistSection(name=section.name, tracks=tracks))
    return PlaylistDefinition(
        name=result.playlist_name,
        sections=tuple(sections),
        description="Importée depuis Resonance.",
    )


def track_add_results_to_import_state(
    playlist_name: str,
    results: list[TrackAddResult],
    *,
    phase: ImportPhase = ImportPhase.COMPLETED,
) -> ImportResultState:
    outcomes = tuple(
        ImportTrackOutcome(
            artist=item.track.artist,
            title=item.track.title,
            section=item.track.section,
            status=_map_track_add_status(item.status),
            message=item.error,
        )
        for item in results
    )
    return ImportResultState(playlist_name=playlist_name, outcomes=outcomes, phase=phase)


def _build_seeds(
    seeds: tuple[SeedReference, ...],
    keywords: tuple[str, ...],
) -> tuple[SeedTrack, ...]:
    parsed: list[SeedTrack] = []
    for seed in seeds:
        artist = seed.artist.strip()
        title = seed.title.strip()
        if not artist and not title:
            continue
        parsed.append(
            SeedTrack(
                TrackRef(artist=artist or title, title=title or artist),
                weight=seed.weight,
            )
        )
    if parsed:
        return tuple(parsed)
    if keywords:
        anchor = keywords[0].strip()
        return (SeedTrack(TrackRef(artist=anchor, title=anchor), weight=1.0),)
    return ()


def _score_to_confidence(score: float) -> ConfidenceLevel:
    if score >= 80.0:
        return ConfidenceLevel.HIGH
    if score >= 50.0:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _map_track_add_status(status: TrackAddStatus) -> ImportTrackStatus:
    return {
        TrackAddStatus.ADDED: ImportTrackStatus.ADDED,
        TrackAddStatus.SKIPPED: ImportTrackStatus.SKIPPED,
        TrackAddStatus.NOT_FOUND: ImportTrackStatus.NOT_FOUND,
        TrackAddStatus.ERROR: ImportTrackStatus.ERROR,
    }[status]
