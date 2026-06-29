from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from playlist_builder.cli.generate_args import (
    build_playlist_request,
    parse_csv_terms,
    parse_exclusion_rule,
    parse_inclusion_rule,
    parse_seed_track,
)
from playlist_builder.cli.generate_playlist import main
from playlist_builder.core.models import TrackRef
from playlist_builder.discovery.providers import StaticCandidateProvider
from playlist_builder.discovery.pipeline import DiscoveryPipeline
from playlist_builder.planning.models import (
    CandidateTrack,
    ConstraintKind,
    EnergyProfile,
    GeneratedPlaylist,
    GenerationConstraints,
    PlaylistRequest,
    SeedTrack,
)
from playlist_builder.playlists.exporter import export_playlist_dict, export_playlist_json
from playlist_builder.playlists.loader import load_playlist
from playlist_builder.session.engine import GenerationSessionEngine
from playlist_builder.session.models import GenerationSession


def test_parse_seed_track_colon_format():
    seed = parse_seed_track("Kygo:Firestone")
    assert seed.track == TrackRef("Kygo", "Firestone")


def test_parse_seed_track_dash_format():
    seed = parse_seed_track("Avicii - Levels")
    assert seed.track == TrackRef("Avicii", "Levels")


def test_parse_seed_track_rejects_empty():
    with pytest.raises(ValueError, match="vide"):
        parse_seed_track("   ")


def test_parse_csv_terms_splits_and_trims():
    assert parse_csv_terms("tropical, dance ,rising") == ("tropical", "dance", "rising")


def test_parse_exclusion_rule_supports_kind_prefix():
    rule = parse_exclusion_rule("artist:Pitbull")
    assert rule.kind == ConstraintKind.ARTIST
    assert rule.value == "Pitbull"


def test_parse_inclusion_rule_supports_weight():
    rule = parse_inclusion_rule("genre:OST:2")
    assert rule.kind == ConstraintKind.GENRE
    assert rule.value == "OST"
    assert rule.weight == 2.0


def test_build_playlist_request_requires_target():
    with pytest.raises(ValueError, match="--tracks ou --duration"):
        build_playlist_request(name="Test", seeds=["Kygo:Firestone"])


def test_export_playlist_json_round_trips_through_loader(tmp_path):
    request = PlaylistRequest(
        name="Pool Party",
        seeds=(SeedTrack(TrackRef("Kygo", "Firestone")),),
        constraints=GenerationConstraints(target_track_count=2),
        description="Generated for tests",
    )
    generated = GeneratedPlaylist(
        request=request,
        candidates=(
            CandidateTrack(TrackRef("Kygo", "Firestone"), score=100, source="seed", reasons=("seed",)),
            CandidateTrack(TrackRef("Avicii", "Levels"), score=80),
        ),
    )

    payload = export_playlist_dict(generated)
    assert payload["name"] == "Pool Party"
    assert payload["sections"][0]["songs"][0] == {"artist": "Kygo", "title": "Firestone"}

    path = tmp_path / "generated.json"
    path.write_text(export_playlist_json(generated), encoding="utf-8")
    playlist = load_playlist(path)

    assert playlist.name == "Pool Party"
    assert len(playlist.tracks) == 2
    assert playlist.tracks[0].artist == "Kygo"


def test_generate_cli_no_catalog_writes_json(tmp_path):
    output = tmp_path / "out.json"
    exit_code = main(
        [
            "--name",
            "CLI Test",
            "--seed",
            "Kygo:Firestone",
            "--tracks",
            "1",
            "--no-catalog",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["name"] == "CLI Test"
    assert data["sections"][0]["songs"] == [{"artist": "Kygo", "title": "Firestone"}]


def test_generate_cli_dry_run_does_not_write(tmp_path):
    output = tmp_path / "out.json"
    exit_code = main(
        [
            "--name",
            "Dry Run",
            "--seed",
            "Kygo:Firestone",
            "--duration",
            "30",
            "--no-catalog",
            "--dry-run",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert not output.exists()


@patch("playlist_builder.cli.generate_playlist.GenerationSessionEngine.generate")
def test_generate_cli_uses_catalog_by_default(mock_generate, tmp_path):
    request = build_playlist_request(
        name="Catalog",
        seeds=["Kygo:Firestone"],
        track_count=2,
        energy_profile=EnergyProfile.RISING,
    )
    generated = GeneratedPlaylist(
        request=request,
        candidates=(CandidateTrack(TrackRef("Kygo", "Firestone"), score=100, source="seed", reasons=("seed",)),),
    )
    mock_generate.return_value = GenerationSession(
        request=request,
        generated_playlist=generated,
        report="🧪 Rapport du labo musical",
    )

    output = tmp_path / "catalog.json"
    with patch("playlist_builder.cli.generate_playlist.ITunesCandidateProvider") as provider_cls:
        provider_cls.return_value = MagicMock()
        exit_code = main(
            [
                "--name",
                "Catalog",
                "--seed",
                "Kygo:Firestone",
                "--tracks",
                "2",
                "--output",
                str(output),
            ]
        )

    assert exit_code == 0
    mock_generate.assert_called_once()
    assert output.exists()


def test_generation_session_engine_with_static_provider():
    request = PlaylistRequest(
        name="Static",
        seeds=(SeedTrack(TrackRef("Kygo", "Firestone")),),
        constraints=GenerationConstraints(
            target_track_count=2,
            preferred_terms=("tropical",),
        ),
    )
    provider = StaticCandidateProvider([
        CandidateTrack(TrackRef("Avicii", "Levels"), score=80, genre="Dance"),
    ])
    session = GenerationSessionEngine(DiscoveryPipeline([provider])).generate(request)

    assert session.generated_playlist.tracks[0] == TrackRef("Kygo", "Firestone")
