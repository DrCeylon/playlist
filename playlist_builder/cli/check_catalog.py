from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playlist_builder.app import AppSettings, build_app_context
from playlist_builder.app.use_cases.check_catalog import CheckCatalogUseCase
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

    context = build_app_context(
        AppSettings(
            country_code=args.country,
            catalog_cache_path=args.cache,
            use_catalog_cache=not args.no_cache,
            acquire_missing_from_catalog=False,
        )
    )
    use_case = CheckCatalogUseCase(context)

    print(f"🎧 {playlist.name}")
    print(f"🔎 Vérification catalogue Apple/iTunes: {len(playlist.tracks)} morceaux")

    result = use_case.execute(playlist)
    for index, match in enumerate(result.matches, 1):
        if match.found:
            print(f"✅ {index:03d}/{len(result.matches)} {match.query.label}")
        elif match.error:
            print(f"⚠️  {index:03d}/{len(result.matches)} {match.query.label}: {match.error}")
        else:
            print(f"❌ {index:03d}/{len(result.matches)} {match.query.label}")

    csv_path, html_path = write_catalog_reports(playlist.name, list(result.matches), Path("reports"))
    found = sum(1 for match in result.matches if match.found)

    print("\nTerminé.")
    print(f"✅ Correspondances catalogue: {found}/{len(result.matches)}")
    print(f"📄 CSV: {csv_path}")
    print(f"🌐 HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
