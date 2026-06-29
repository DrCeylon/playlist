from __future__ import annotations

import argparse
from pathlib import Path

from playlist_builder.catalog.apple_search import AppleCatalogSearch
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.catalog.rate_limiter import RateLimiter
from playlist_builder.catalog.retry_policy import RetryPolicy
from playlist_builder.playlists.loader import load_playlist
from playlist_builder.reports.catalog_report import CatalogReportWriter

DEFAULT_PLAYLIST = Path("playlists/orlando_pool_party_2026.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check tracks against the Apple/iTunes public catalog.")
    parser.add_argument("--playlist", type=Path, default=DEFAULT_PLAYLIST)
    parser.add_argument("--country", default="us")
    parser.add_argument("--interval", type=float, default=2.5, help="Minimum interval between catalog calls")
    parser.add_argument("--base-delay", type=float, default=2.0, help="Initial retry minimum delay")
    parser.add_argument("--increment", type=float, default=3.0, help="Retry minimum delay increment")
    parser.add_argument("--max-min-delay", type=float, default=30.0, help="Maximum retry minimum delay")
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--max-total-wait", type=float, default=300.0)
    args = parser.parse_args()

    playlist_name, tracks = load_playlist(args.playlist)
    cache = JsonCache(Path("cache/catalog.json"))
    search = AppleCatalogSearch(
        country=args.country,
        cache=cache,
        rate_limiter=RateLimiter(minimum_interval_seconds=args.interval),
        retry_policy=RetryPolicy(
            base_min_delay=args.base_delay,
            increment=args.increment,
            max_min_delay=args.max_min_delay,
            max_attempts=args.max_attempts,
            max_total_wait=args.max_total_wait,
        ),
    )

    print(f"🎧 {playlist_name}")
    print(f"🔎 Vérification catalogue: {len(tracks)} morceaux")

    matches = []
    for index, track in enumerate(tracks, 1):
        match = search.search_track(track)
        matches.append(match)
        if match.found:
            print(f"✅ {index:03d}/{len(tracks)} {track.label}")
        elif match.error:
            print(f"⚠️  {index:03d}/{len(tracks)} {track.label}: {match.error}")
        else:
            print(f"❌ {index:03d}/{len(tracks)} {track.label}")

    csv_path, html_path = CatalogReportWriter().write(playlist_name, matches)
    found = sum(1 for match in matches if match.found)

    print("\nTerminé.")
    print(f"✅ Correspondances catalogue: {found}/{len(matches)}")
    print(f"📄 CSV: {csv_path}")
    print(f"🌐 HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
