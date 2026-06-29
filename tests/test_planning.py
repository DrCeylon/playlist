from playlist_builder.core.models import TrackRef
from playlist_builder.planning.models import GenerationConstraints, PlaylistRequest, SeedTrack
from playlist_builder.planning.planner import PlaylistPlanner


def test_planner_returns_seed_tracks_in_generation_contract():
    request = PlaylistRequest(
        name="Zelda",
        seeds=(SeedTrack(TrackRef("Koji Kondo", "Gerudo Valley")),),
        constraints=GenerationConstraints(target_track_count=1, preferred_terms=("Gerudo",)),
    )

    result = PlaylistPlanner().plan_from_seeds_only(request)

    assert result.tracks == [TrackRef("Koji Kondo", "Gerudo Valley")]


def test_request_requires_seed():
    request = PlaylistRequest(
        name="Empty",
        seeds=(),
        constraints=GenerationConstraints(target_track_count=1),
    )

    try:
        request.validate()
    except ValueError as exc:
        assert "morceau de référence" in str(exc)
    else:
        raise AssertionError("Validation should have failed")
