from __future__ import annotations

from pathlib import Path

from playlist_builder.catalog.cache import JsonCache


def test_json_cache_defers_flush_until_requested(tmp_path: Path):
    cache_path = tmp_path / "cache.json"
    cache = JsonCache(cache_path)
    cache.set("a", {"value": 1})
    assert not cache_path.exists()

    cache.flush()
    assert cache_path.exists()
    reloaded = JsonCache(cache_path)
    assert reloaded.get("a") == {"value": 1}


def test_json_cache_context_manager_flushes(tmp_path: Path):
    cache_path = tmp_path / "cache.json"
    with JsonCache(cache_path) as cache:
        cache.set("b", 2)
    reloaded = JsonCache(cache_path)
    assert reloaded.get("b") == 2
