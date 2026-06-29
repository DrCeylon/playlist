from playlist_builder.core.models import TrackAddStatus, TrackRef
from playlist_builder.music.client import MusicClient
from playlist_builder.resolver.constants import CANDIDATE_DELIMITER, FIELD_DELIMITER, RESULT_DELIMITER
from playlist_builder.resolver.models import ResolverCandidate
from playlist_builder.resolver.selection import rank_candidates, select_best_candidate


def test_select_best_candidate_uses_python_scoring():
    wanted = TrackRef("Koji Kondo", "Gerudo Valley")
    candidates = [
        ResolverCandidate(wanted, "Mariah Carey", "Fantasy", "bad"),
        ResolverCandidate(wanted, "Nintendo Sound Team", "Gerudo Valley", "good"),
    ]

    decision = select_best_candidate(wanted, candidates)

    assert decision.found
    assert decision.selected is not None
    assert decision.selected.persistent_id == "good"
    assert decision.confidence >= 70


def test_select_best_candidate_rejects_low_confidence_candidates():
    wanted = TrackRef("Koji Kondo", "Gerudo Valley")
    decision = select_best_candidate(
        wanted,
        [ResolverCandidate(wanted, "Mariah Carey", "Fantasy", "bad")],
    )

    assert not decision.found
    assert decision.selected is None


def test_rank_candidates_deduplicates_artist_title_pairs():
    wanted = TrackRef("Koji Kondo", "Gerudo Valley")
    ranked = rank_candidates(
        wanted,
        [
            ResolverCandidate(wanted, "Nintendo", "Gerudo Valley", "1"),
            ResolverCandidate(wanted, "Nintendo", "Gerudo Valley", "2"),
        ],
    )

    assert len(ranked) == 1


def test_parse_candidates_from_applescript_payload():
    wanted = TrackRef("Koji Kondo", "Gerudo Valley")
    row = CANDIDATE_DELIMITER.join(
        [
            FIELD_DELIMITER.join(["Nintendo", "Gerudo Valley", "ABC", "Gerudo"]),
            FIELD_DELIMITER.join(["Mariah Carey", "Fantasy", "XYZ", "Fantasy"]),
        ]
    )

    candidates = MusicClient._parse_candidates(wanted, row)

    assert [candidate.persistent_id for candidate in candidates] == ["ABC", "XYZ"]


def test_collect_single_candidate_row_accepts_empty_output(monkeypatch):
    client = MusicClient()

    monkeypatch.setattr("playlist_builder.music.client.run_applescript", lambda script: "")

    assert client._collect_single_candidate_row(TrackRef("A", "B")) == ""


def test_collect_single_candidate_row_takes_first_row(monkeypatch):
    client = MusicClient()
    output = RESULT_DELIMITER.join(["first", "second"])

    monkeypatch.setattr("playlist_builder.music.client.run_applescript", lambda script: output)

    assert client._collect_single_candidate_row(TrackRef("A", "B")) == "first"


def test_collect_candidate_rows_is_per_track(monkeypatch):
    client = MusicClient()
    calls = []

    def fake_collect(track):
        calls.append(track.title)
        return track.title

    monkeypatch.setattr(client, "_collect_single_candidate_row", fake_collect)

    rows = client._collect_candidate_rows([TrackRef("A", "One"), TrackRef("B", "Two")])

    assert rows == ["One", "Two"]
    assert calls == ["One", "Two"]


def test_add_tracks_batch_uses_selected_candidate_ids(monkeypatch):
    client = MusicClient()
    wanted = TrackRef("Koji Kondo", "Gerudo Valley")
    row = FIELD_DELIMITER.join(["Nintendo", "Gerudo Valley", "ABC", "Gerudo"])

    monkeypatch.setattr(client, "_collect_candidate_rows", lambda tracks: [row])
    monkeypatch.setattr(client, "_duplicate_selected_tracks", lambda playlist, ids: ["added"])

    result = client._add_tracks_batch("Zelda", [wanted])

    assert result[0].status == TrackAddStatus.ADDED


def test_add_tracks_batch_reports_not_found_when_no_candidate(monkeypatch):
    client = MusicClient()
    wanted = TrackRef("Koji Kondo", "Gerudo Valley")

    monkeypatch.setattr(client, "_collect_candidate_rows", lambda tracks: [""])
    monkeypatch.setattr(client, "_duplicate_selected_tracks", lambda playlist, ids: [])

    result = client._add_tracks_batch("Zelda", [wanted])

    assert result[0].status == TrackAddStatus.NOT_FOUND
