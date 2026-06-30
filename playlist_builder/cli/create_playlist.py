from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playlist_builder.app import AppSettings, build_app_context
from playlist_builder.app.use_cases.import_playlist import ImportPlaylistUseCase
from playlist_builder.catalog.cache import JsonCache
from playlist_builder.core.models import TrackAddStatus
from playlist_builder.core.platform import require_macos
from playlist_builder.music.musickit_client import MusicKitClient, MusicKitConfigurationError
from playlist_builder.playlists.loader import PlaylistValidationError, load_playlist
from playlist_builder.reports.playlist import write_playlist_report

DEFAULT_PLAYLIST = Path("playlists/orlando_pool_party_2026.json")
DEFAULT_MUSICKIT_CACHE = Path("cache/musickit_catalog.json")
DEFAULT_IDENTITY_CACHE = Path("cache/apple_music_identity.json")
DEFAULT_CATALOG_CACHE = Path("cache/itunes_catalog.json")
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
    parser.add_argument("--country", default="us", help="Store country for catalog acquisition, e.g. us, ch, fr")
    parser.add_argument(
        "--cache",
        type=Path,
        default=DEFAULT_MUSICKIT_CACHE,
        help="JSON cache file for MusicKit catalog lookups.",
    )
    parser.add_argument(
        "--catalog-cache",
        type=Path,
        default=DEFAULT_CATALOG_CACHE,
        help="JSON cache file for iTunes catalog lookups used during acquisition.",
    )
    parser.add_argument("--no-cache", action="store_true", help="Disable MusicKit catalog caching.")
    parser.add_argument(
        "--identity-cache",
        type=Path,
        default=DEFAULT_IDENTITY_CACHE,
        help="JSON cache file for Apple Music identity resolution mappings.",
    )
    parser.add_argument(
        "--no-acquire",
        action="store_true",
        help="Ne tente pas d'ajouter automatiquement les morceaux manquants depuis le catalogue iTunes.",
    )
    parser.add_argument(
        "--no-wait-for-acquisition",
        action="store_true",
        help="N'attend pas de confirmation manuelle après ouverture d'une URL catalogue dans Music.app.",
    )
    parser.add_argument(
        "--json-diagnostics",
        action="store_true",
        help="Écrit un rapport JSON détaillé dans reports/.",
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
        country=args.country,
        identity_cache_path=args.identity_cache,
        catalog_cache_path=args.catalog_cache,
        acquire_missing=not args.no_acquire,
        wait_for_manual_catalog_add=not args.no_wait_for_acquisition,
        write_json_diagnostics=args.json_diagnostics,
    )


def _print_dry_run(playlist) -> None:
    index = 1
    for section in playlist.sections:
        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{section.name}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for track in section.tracks:
            print(f"{index:03d}. [{track.section}] {track.label}")
            index += 1


def _run_musickit(playlist, storefront, cache_path, no_cache, allow_duplicates) -> int:
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
    playlist,
    *,
    incremental: bool,
    allow_duplicates: bool,
    country: str,
    identity_cache_path: Path,
    catalog_cache_path: Path,
    acquire_missing: bool,
    wait_for_manual_catalog_add: bool,
    write_json_diagnostics: bool,
) -> int:
    require_macos("l'application Music")

    context = build_app_context(
        AppSettings(
            country_code=country,
            identity_cache_path=identity_cache_path,
            catalog_cache_path=catalog_cache_path,
            acquire_missing_from_catalog=acquire_missing,
            wait_for_manual_catalog_add=wait_for_manual_catalog_add,
        )
    )
    use_case = ImportPlaylistUseCase(context)

    if incremental:
        existing_keys = None if allow_duplicates else context.apple_music.import_service.applescript.load_playlist_keys(playlist.name)
        context.apple_music.import_service.applescript.ensure_running()
        context.apple_music.import_service.applescript.ensure_playlist(playlist.name)
        result = use_case.execute(
            playlist,
            sync=False,
            existing_keys=existing_keys,
            allow_duplicates=allow_duplicates,
            write_json_diagnostics=write_json_diagnostics,
        )
    else:
        print("🔁 Synchronisation de la playlist selon l'ordre des sections du JSON...")
        if acquire_missing:
            print("📥 Acquisition catalogue→bibliothèque activée pour les morceaux manquants")
        if acquire_missing and wait_for_manual_catalog_add:
            print("⏸️  Le programme attendra Entrée si un ajout manuel dans Music.app est requis")
        result = use_case.execute(
            playlist,
            sync=True,
            write_json_diagnostics=write_json_diagnostics,
        )

    _print_results(playlist.tracks, list(result.track_results))
    return _write_summary(playlist.name, list(result.track_results), result.text_report_path, result.json_report_path)


def _print_results(tracks, ordered_results) -> None:
    current_section = None
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


def _write_summary(playlist_name, ordered_results, text_report=None, json_report=None) -> int:
    report = text_report or write_playlist_report(playlist_name, ordered_results, Path("reports"))
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
    if json_report:
        print(f"🧾 Diagnostics JSON: {json_report}")
    return 0 if errors == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
