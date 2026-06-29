from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playlist_builder.catalog.cache import JsonCache
from playlist_builder.core.models import PlaylistDefinition, TrackAddStatus, TrackRef
from playlist_builder.core.platform import require_macos
from playlist_builder.music.client import MusicClient
from playlist_builder.music.musickit_client import MusicKitClient, MusicKitConfigurationError
from playlist_builder.playlists.loader import PlaylistValidationError, load_playlist
from playlist_builder.reports.playlist import write_playlist_report

DEFAULT_PLAYLIST = Path("playlists/orlando_pool_party_2026.json")
DEFAULT_MUSICKIT_CACHE = Path("cache/musickit_catalog.json")
MUSICKIT_EXPERIMENTAL_NOTICE = (
    "MusicKit est expérimental et nécessite un compte Apple Developer payant (99 USD/an). "
    "Le workflow recommandé reste AppleScript + check_catalog.py."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create Apple Music playlists from JSON files.")
    parser.add_argument("--playlist", type=Path, default=DEFAULT_PLAYLIST)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Ajoute uniquement les morceaux manquants sans réordonner la playlist.",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="En mode incrémental, autorise les doublons. Ignoré en mode sync (défaut).",
    )
    parser.add_argument(
        "--engine",
        choices=["applescript", "musickit"],
        default="applescript",
        help="Moteur de création. applescript (recommandé) ou musickit (expérimental, licence payante).",
    )
    parser.add_argument("--storefront", default="us", help="Apple Music storefront for MusicKit, e.g. us, ch, fr")
    parser.add_argument(
        "--cache",
        type=Path,
        default=DEFAULT_MUSICKIT_CACHE,
        help="JSON cache file for MusicKit catalog lookups.",
    )
    parser.add_argument("--no-cache", action="store_true", help="Disable MusicKit catalog caching.")
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

    print(f"🎧 Playlist: {playlist.name}")
    print(f"🎵 Morceaux: {len(playlist.tracks)}")
    print(f"📂 Sections: {len(playlist.sections)}")

    if args.dry_run:
        _print_dry_run(playlist)
        return 0

    if args.engine == "musickit":
        print(f"⚠️  {MUSICKIT_EXPERIMENTAL_NOTICE}", file=sys.stderr)
        return _run_musickit(playlist, args.storefront, args.cache, args.no_cache, args.allow_duplicates)

    return _run_applescript(
        playlist,
        incremental=args.incremental,
        allow_duplicates=args.allow_duplicates,
    )


def _print_dry_run(playlist: PlaylistDefinition) -> None:
    index = 1
    for section in playlist.sections:
        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{section.name}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for track in section.tracks:
            print(f"{index:03d}. [{track.section}] {track.label}")
            index += 1


def _run_musickit(
    playlist: PlaylistDefinition,
    storefront: str,
    cache_path: Path,
    no_cache: bool,
    allow_duplicates: bool,
) -> int:
    cache = None if no_cache else JsonCache(cache_path)
    try:
        client = MusicKitClient.from_env(storefront=storefront, cache=cache)
        ordered_results = client.create_or_update_playlist(
            playlist.name,
            playlist.tracks,
            description=playlist.description,
            allow_duplicates=allow_duplicates,
        )
    except MusicKitConfigurationError as exc:
        print(f"Configuration MusicKit manquante: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"Erreur MusicKit: {exc}", file=sys.stderr)
        return 3
    finally:
        if cache:
            cache.flush()

    _print_results(playlist.tracks, ordered_results)
    return _write_summary(playlist.name, ordered_results)


def _run_applescript(
    playlist: PlaylistDefinition,
    *,
    incremental: bool,
    allow_duplicates: bool,
) -> int:
    require_macos("l'application Music")

    client = MusicClient()
    client.ensure_running()
    client.ensure_playlist(playlist.name)

    if incremental:
        existing_keys = None if allow_duplicates else client.load_playlist_keys(playlist.name)
        ordered_results = client.add_tracks(
            playlist.name,
            playlist.tracks,
            existing_keys=existing_keys,
            allow_duplicates=allow_duplicates,
        )
    else:
        print("🔁 Synchronisation de la playlist selon l'ordre des sections du JSON...")
        ordered_results = client.sync_playlist_order(playlist.name, playlist.tracks)

    _print_results(playlist.tracks, ordered_results)
    return _write_summary(playlist.name, ordered_results)


def _print_results(tracks: list[TrackRef], ordered_results) -> None:
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
