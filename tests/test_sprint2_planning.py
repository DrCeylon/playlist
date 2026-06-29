from playlist_builder.core.models import TrackRef
from playlist_builder.planning.analyzer import PlaylistAnalyzer
from playlist_builder.planning.models import (
    CandidateTrack,
    ConstraintKind,
    EnergyProfile,
    ExclusionRule,
    GenerationConstraints,
    InclusionRule,
    PlaylistRequest,
    SeedTrack,
)
from playlist_builder.planning.planner import PlaylistPlanner
from playlist_builder.planning.report import build_mad_scientist_report


def test_structured_exclusion_rejects_artist():
    request = PlaylistRequest(
        name="Pool Party",
        seeds=(SeedTrack(TrackRef("Kygo", "Firestone")),),
        constraints=GenerationConstraints(
            target_track_count=2,
            exclusions=(ExclusionRule(ConstraintKind.ARTIST, "Pitbull"),),
        ),
    )
    candidates = [
        CandidateTrack(TrackRef("Kygo", "Firestone"), score=100, source="seed", reasons=("seed",)),
        CandidateTrack(TrackRef("Pitbull", "Give Me Everything"), score=80),
        CandidateTrack(TrackRef("Avicii", "Levels"), score=70),
    ]

    result = PlaylistPlanner().plan(request, candidates)

    assert result.tracks == [TrackRef("Kygo", "Firestone"), TrackRef("Avicii", "Levels")]
    assert result.rejected[0].track == TrackRef("Pitbull", "Give Me Everything")


def test_structured_exclusion_rejects_genre_from_catalog_metadata():
    request = PlaylistRequest(
        name="No Soundtrack",
        seeds=(SeedTrack(TrackRef("Kygo", "Firestone")),),
        constraints=GenerationConstraints(
            target_track_count=2,
            exclusions=(ExclusionRule(ConstraintKind.GENRE, "Soundtrack"),),
        ),
    )
    candidates = [
        CandidateTrack(TrackRef("Kygo", "Firestone"), score=100, source="seed", reasons=("seed",)),
        CandidateTrack(TrackRef("Koji Kondo", "Gerudo Valley"), score=80, genre="Soundtrack"),
        CandidateTrack(TrackRef("Avicii", "Levels"), score=70, genre="Dance"),
    ]

    result = PlaylistPlanner().plan(request, candidates)

    assert result.tracks == [TrackRef("Kygo", "Firestone"), TrackRef("Avicii", "Levels")]
    assert result.rejected[0].genre == "Soundtrack"


def test_planner_uses_duration_when_track_count_missing():
    request = PlaylistRequest(
        name="Duration",
        seeds=(SeedTrack(TrackRef("A", "One")),),
        constraints=GenerationConstraints(target_duration_minutes=7),
    )
    candidates = [
        CandidateTrack(TrackRef("A", "One"), score=100, source="seed", reasons=("seed",)),
        CandidateTrack(TrackRef("B", "Two"), score=90),
        CandidateTrack(TrackRef("C", "Three"), score=80),
    ]

    result = PlaylistPlanner().plan(request, candidates)

    assert len(result.tracks) == 2


def test_structured_inclusion_boosts_candidate():
    request = PlaylistRequest(
        name="Zelda",
        seeds=(SeedTrack(TrackRef("Koji Kondo", "Gerudo Valley")),),
        constraints=GenerationConstraints(
            target_track_count=1,
            inclusions=(InclusionRule(ConstraintKind.MOOD, "adventure", weight=2),),
        ),
    )
    candidates = [
        CandidateTrack(TrackRef("Artist A", "Track A"), score=50, mood="ambient"),
        CandidateTrack(TrackRef("Artist B", "Track B"), score=20, mood="adventure"),
    ]

    result = PlaylistPlanner().plan(request, candidates)

    assert result.tracks == [TrackRef("Artist B", "Track B")]


def test_report_has_mad_scientist_tone_and_suggestions():
    request = PlaylistRequest(
        name="Laboratoire Zelda",
        seeds=(SeedTrack(TrackRef("Koji Kondo", "Gerudo Valley")),),
        constraints=GenerationConstraints(
            target_track_count=1,
            energy_profile=EnergyProfile.RISING,
        ),
    )
    candidates = [
        CandidateTrack(TrackRef("Koji Kondo", "Gerudo Valley"), score=100, source="seed", reasons=("seed",), genre="OST", mood="adventure"),
        CandidateTrack(TrackRef("Koji Kondo", "Lost Woods"), score=80, genre="OST", mood="mischief"),
    ]

    result = PlaylistPlanner().plan(request, candidates)
    report = build_mad_scientist_report(result)

    assert "🧪 Rapport du labo musical" in report
    assert "Suggestions en réserve : 1" in report
    assert "Importer telle quelle" in report


def test_analyzer_counts_metadata():
    request = PlaylistRequest(
        name="Analysis",
        seeds=(SeedTrack(TrackRef("A", "Seed")),),
        constraints=GenerationConstraints(target_track_count=2),
    )
    result = PlaylistPlanner().plan(
        request,
        [
            CandidateTrack(TrackRef("A", "Seed"), score=100, source="seed", reasons=("seed",), genre="OST", language="ja", energy=40),
            CandidateTrack(TrackRef("B", "Track"), score=80, genre="OST", language="en", energy=80),
        ],
    )

    analysis = PlaylistAnalyzer().analyze(result)

    assert analysis.track_count == 2
    assert analysis.genres == (("OST", 2),)
    assert analysis.average_energy == 60
