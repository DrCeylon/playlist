from playlist_builder.core.models import TrackRef
from playlist_builder.generation.generator import PlaylistGenerator
from playlist_builder.generation.models import GenerationConstraint, PlaylistCandidate, PlaylistRequest


def test_generator_preserves_seed_tracks_first_and_removes_duplicates():
    seed = TrackRef("Artist A", "Seed Song")
    request = PlaylistRequest(name="Test", seed_tracks=(seed,), constraints=GenerationConstraint(target_track_count=3))
    candidates = [
        PlaylistCandidate(track=seed, score=100, reason="duplicate seed"),
        PlaylistCandidate(track=TrackRef("Artist B", "Candidate 1"), score=90),
        PlaylistCandidate(track=TrackRef("Artist C", "Candidate 2"), score=80),
    ]

    generated = PlaylistGenerator().build(request, candidates)

    assert [track.title for track in generated.tracks] == ["Seed Song", "Candidate 1", "Candidate 2"]
