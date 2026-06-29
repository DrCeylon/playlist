from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playlist_builder.core.models import TrackAddStatus
from playlist_builder.core.platform import require_macos
from playlist_builder.music.client import MusicClient
from playlist_builder.music.musickit_client import MusicKitClient, MusicKitConfigurationError
from playlist_builder.playlists.loader import PlaylistValidationError, load_playlist
from playlist_builder.reports.playlist import write_playlist_report

DEFAULT_PLAYLIST = Path("playlists/orlando_pool_party_2026.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create Apple Music playlists from JSON files.")
    parser.add_argument("--playlist", type=Path, default=DEFAULT_PLAYLIST)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-duplicates", action="store_true")
    parser.add_argument("--engine", choices=["applescript", "musickit"], default="applescript")
    parser.add_argument("--storefront", default="us", help="Apple Music storefront for MusicKit, e.g. us, ch, fr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.playlist.exists():
        print(f"Fichier introuvable: {args.playlist}", file=sys.stderr)
        return 1

    try:
        playlist_name, tracks = load_playlist(args.playlist)
    except PlaylistValidationError as exc:
        print(f"Playlist invalide: {exc}", file=sys.stderr)
        return 1

    print(f"🎧 Playlist: {playlist_name}")
    print(f"🎵 Morceaux: {len(tracks)}")

    if args.dry_run:
        for index, track in enumerate(tracks, 1):
            print(f"{index:03d}. [{track.section}] {track.label}")
        return 0

    if args.engine == "musickit":
        return _run_musickit(playlist_name, tracks, args.storefront)

    return _run_applescript(playlist_name, tracks, allow_duplicates=args.allow_duplicates)


def _run_musickit(playlist_name: str, tracks, storefront: str) -> int:
    try:
        client = MusicKitClient.from_env(storefront=storefront)
        ordered_results = client.create_or_update_playlist(playlist_name, tracks)
    except MusicKitConfigurationError as exc:
        print(f"Configuration MusicKit manquante: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"Erreur MusicKit: {exc}", file=sys.stderr)
        return 3

    _print_results(tracks, ordered_results)
    return _write_summary(playlist_name, ordered_results)


def _run_applescript(playlist_name: str, tracks, *, allow_duplicates: bool) -> int:
    require_macos("l'application Music")

    client = MusicClient()
    client.ensure_running()
    client.ensure_playlist(playlist_name)

    existing_keys = None if allow_duplicates else client.load_playlist_keys(playlist_name)
    ordered_results = client.add_tracks(
        playlist_name,
        tracks,
        existing_keys=existing_keys,
        allow_duplicates=allow_duplicates,
    )

    _print_results(tracks, ordered_results)
    return _write_summary(playlist_name, ordered_results)


def _print_results(tracks, ordered_results) -> None:
    current_section: str | None = None
    for index, result in enumerate(ordered_results, 1):
        if result.track.section != current_section:
            current_section = result.track.section
            print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{current_section}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        label = f"{index:03d}/{len(tracks)} {result.track.label}"
        if result.status == TrackAddStatus.SKIPPED:
            print(f"⏭️  {label}")
        elif result.status == TrackAddStatus.ADDED:
            print(f"✅ {label}")
        elif result.status == TrackAddStatus.ERROR:
            print(f"⚠️  {label} — {result.error}")
        else:
            suffix = f" — {result.error}" if result.error else ""
            print(f"❌ {label}{suffix}")


def _write_summary(playlist_name: str, ordered_results) -> int:
    report = write_playlist_report(playlist_name, ordered_results, Path("reports"))
    added = sum(1 for result in ordered_results if result.status == TrackAddStatus.ADDED)
    skipped = sum(1 for result in ordered_results if result.status == TrackAddStatus.SKIPPED)
    not_found = sum(1 for result in ordered_results if result.status == TrackAddStatus.NOT_FOUND)
    errors = sum(1 for result in ordered_results if result.status == TrackAddStatus.ERROR)

    print("\nTerminé.")
    print(f"✅ Ajoutés: {added}")
    print(f"⏭️  Déjà présents: {skipped}")
    print(f"❌ Non trouvés: {not_found}")
    if errors:
        print(f"⚠️  Erreurs: {errors}")
    print(f"📄 Rapport: {report}")
    return 0 if errors == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
