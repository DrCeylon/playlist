from __future__ import annotations

from playlist_builder.integration.apple_music.applescript_client import AppleScriptClient


def test_catalog_acquire_urls_includes_music_and_itms_fallback():
    urls = AppleScriptClient._catalog_acquire_urls(
        "https://music.apple.com/us/song/firestone/950274258",
        "950274258",
    )
    assert urls[0] == "itms://music.apple.com/song/id950274258"
    assert "https://music.apple.com/song/id950274258" in urls
    assert "https://music.apple.com/us/song/firestone/950274258" in urls
    assert "music://music.apple.com/us/song/firestone/950274258" in urls


def test_catalog_acquire_urls_prioritizes_direct_song_id_urls():
    urls = AppleScriptClient._catalog_acquire_urls(
        "https://music.apple.com/fr/album/derniere-danse/254228726?i=254228761",
        "254228761",
    )
    assert urls[0] == "itms://music.apple.com/song/id254228761"
    assert "https://music.apple.com/song/id254228761" in urls
    assert "https://music.apple.com/fr/album/derniere-danse/254228726?i=254228761" in urls


def test_acquire_script_uses_play_and_duplicate_with_search_terms():
    script = AppleScriptClient._build_acquire_song_script(
        ["https://music.apple.com/us/song/firestone/950274258"],
        search_terms=["Kygo Firestone", "Firestone", "Kygo"],
        play_delay_seconds=5.0,
        settle_delay_seconds=6.0,
    )
    assert "duplicate current track to source \"Library\"" in script
    assert "open location" in script
    assert "Kygo Firestone" in script
    assert "duplicated" in script
