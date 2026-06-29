from playlist_builder.core.models import TrackRef
from playlist_builder.resolver.applescript import build_resolve_batch_script
from playlist_builder.resolver.constants import MAX_QUERY_VARIANTS
from playlist_builder.resolver.normalization import normalize_text, token_set
from playlist_builder.resolver.query import generate_query_variants
from playlist_builder.resolver.scoring import is_acceptable_match, score_candidate, similarity_ratio, token_overlap


def test_normalize_text_removes_accents_noise_and_brackets():
    assert normalize_text("Gérudo Valley (Live) feat. Someone") == "gerudo valley"


def test_token_set_normalizes_ampersand():
    assert token_set("Rock & Roll") == {"rock", "and", "roll"}


def test_query_variants_include_title_artist_and_zelda_aliases():
    variants = generate_query_variants(TrackRef("Koji Kondo", "Gerudo Valley", section="Zelda Adventure"))
    terms = [variant.term for variant in variants]

    assert "Gerudo Valley Koji Kondo" in terms
    assert "Koji Kondo Gerudo Valley" in terms
    assert "Zelda Gerudo Valley" in terms
    assert "Legend of Zelda Gerudo Valley" in terms


def test_query_variants_are_deduplicated():
    variants = generate_query_variants(TrackRef("Koji Kondo", "Gerudo Valley"))
    normalized = [normalize_text(variant.term) for variant in variants]

    assert len(normalized) == len(set(normalized))


def test_query_variants_are_capped():
    variants = generate_query_variants(
        TrackRef("Koji Kondo", "Gerudo Valley", section="Zelda Adventure")
    )

    assert len(variants) <= MAX_QUERY_VARIANTS


def test_build_resolve_batch_script_collects_candidates():
    script = build_resolve_batch_script([TrackRef("Kygo", "Firestone")])

    assert "set candidateRows to {}" in script
    assert "search library playlist 1" in script
    assert "persistent ID of candidateTrack" in script


def test_is_acceptable_match_rejects_unrelated_candidate():
    wanted = TrackRef("Koji Kondo", "Gerudo Valley")
    assert is_acceptable_match(wanted, "Nintendo Sound Team", "Gerudo Valley")
    assert not is_acceptable_match(wanted, "Mariah Carey", "Fantasy")


def test_similarity_ratio_scores_close_titles_higher_than_different_titles():
    close = similarity_ratio("Gerudo Valley", "Gerudo Valley Original Soundtrack")
    far = similarity_ratio("Gerudo Valley", "Fantasy")

    assert close > far


def test_token_overlap_scores_shared_tokens():
    assert token_overlap("Super Mario Bros Main Theme", "Super Mario Main Theme") > 0.5


def test_score_candidate_prioritizes_title_match_even_with_ost_artist_variations():
    good = score_candidate(
        TrackRef("Koji Kondo", "Gerudo Valley"),
        candidate_artist="Nintendo Sound Team",
        candidate_title="Gerudo Valley",
    )
    bad = score_candidate(
        TrackRef("Koji Kondo", "Gerudo Valley"),
        candidate_artist="Mariah Carey",
        candidate_title="Fantasy",
    )

    assert good > bad
    assert good >= 70
