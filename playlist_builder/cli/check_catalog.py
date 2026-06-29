from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playlist_builder.catalog.apple_search import AppleCatalogSearch
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.catalog.rate_limiter import RateLimiter
from playlist_builder.playlists.loader import PlaylistValidationError, load_playlist
from playlist_builder.reports.catalog import write_catalog_reports

DEFAULT_PLAYLIST = Path("playlists/orlando_pool_party_2026.json")
DEFAULT_CACHE = Path("cache/itunes_catalog.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check tracks against Apple Music/iTunes public catalog."
    )
    parser.add_argument("--playlist", type=Path, default=DEFAULT_PLAYLIST)
    parser.add_argument("--country", default="us", help="Store country, e.g. us, ch, fr.")
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Minimum delay between API calls in seconds.",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=DEFAULT_CACHE,
        help="JSON cache file for catalog lookups.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable catalog response caching.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.playlist.exists():
        print(f"Fichier introuvable: {args.playlist}", file=sys.stderr)
        return 1

    try:
        playlist = load_playlist(args.playlist)
    except PlaylistValidationError as exc:
        print(f"Playlist invalide: {exc}", file=sys.stderr)
        return 1

    searcher = AppleCatalogSearch(
        country=args.country,
        cache=None if args.no_cache else JsonCache(args.cache),
        rate_limiter=RateLimiter(minimum_interval_seconds=max(0.0, args.sleep)),
    )

    print(f"🎧 {playlist.name}")
    print(f"🔎 Vérification catalogue Apple/iTunes: {len(playlist.tracks)} morceaux")

    matches = []
    try:
        for index, track in enumerate(playlist.tracks, 1):
            match = searcher.search_track(track)
            matches.append(match)
            if match.found:
                print(f"✅ {index:03d}/{len(playlist.tracks)} {track.label}")
            elif match.error:
                print(f"⚠️  {index:03d}/{len(playlist.tracks)} {track.label}: {match.error}")
            else:
                print(f"❌ {index:03d}/{len(playlist.tracks)} {track.label}")
    finally:
        if searcher.cache:
            searcher.cache.flush()

    csv_path, html_path = write_catalog_reports(playlist.name, matches, Path("reports"))
    found = sum(1 for match in matches if match.found)

    print("\nTerminé.")
    print(f"✅ Correspondances catalogue: {found}/{len(matches)}")
    print(f"📄 CSV: {csv_path}")
    print(f"🌐 HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
