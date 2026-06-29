#!/usr/bin/env python3
"""
Apple Music Playlist Builder.

Crée une playlist Apple Music locale à partir d'un fichier JSON.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_PLAYLIST = Path("playlists/orlando_pool_party_2026.json")

@dataclass(frozen=True)
class Song:
    artist: str
    title: str
    section: str


def apple_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def run_applescript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def ensure_music_running() -> None:
    run_applescript('tell application "Music" to activate')


def ensure_playlist(name: str) -> None:
    n = apple_escape(name)
    run_applescript(f'''
tell application "Music"
    if not (exists user playlist "{n}") then
        make new user playlist with properties {{name:"{n}"}}
    end if
end tell
''')


def playlist_contains(playlist_name: str, song: Song) -> bool:
    p = apple_escape(playlist_name)
    title = apple_escape(song.title)
    artist = apple_escape(song.artist)
    script = f'''
tell application "Music"
    try
        set matches to every track of user playlist "{p}" whose name is "{title}" and artist is "{artist}"
        if (count of matches) > 0 then
            return "true"
        else
            return "false"
        end if
    on error
        return "false"
    end try
end tell
'''
    return run_applescript(script).lower() == "true"


def add_song(playlist_name: str, song: Song) -> bool:
    p = apple_escape(playlist_name)
    title = apple_escape(song.title)
    artist = apple_escape(song.artist)
    script = f'''
tell application "Music"
    set targetPlaylist to user playlist "{p}"
    try
        set foundTrack to first track of library playlist 1 whose name is "{title}" and artist is "{artist}"
        duplicate foundTrack to targetPlaylist
        return "added"
    on error
        try
            set foundTrack to first track of library playlist 1 whose name contains "{title}" and artist contains "{artist}"
            duplicate foundTrack to targetPlaylist
            return "added"
        on error
            return "not_found"
        end try
    end try
end tell
'''
    return run_applescript(script) == "added"


def load_songs(path: Path) -> tuple[str, list[Song]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    songs: list[Song] = []
    for section in data.get("sections", []):
        section_name = section.get("name", "Playlist")
        for item in section.get("songs", []):
            songs.append(Song(artist=item["artist"], title=item["title"], section=section_name))
    return data["name"], songs


def write_report(playlist_name: str, not_found: list[Song], skipped: list[Song]) -> Path:
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    path = reports / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    lines = [f"Playlist: {playlist_name}", f"Generated: {datetime.now().isoformat(timespec='seconds')}", "", f"Not found: {len(not_found)}"]
    lines += [f"- [{s.section}] {s.artist} - {s.title}" for s in not_found]
    lines += ["", f"Already present / skipped: {len(skipped)}"]
    lines += [f"- [{s.section}] {s.artist} - {s.title}" for s in skipped]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Apple Music playlists from JSON files.")
    parser.add_argument("--playlist", type=Path, default=DEFAULT_PLAYLIST)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-duplicates", action="store_true")
    args = parser.parse_args()

    if not args.playlist.exists():
        print(f"Fichier introuvable: {args.playlist}", file=sys.stderr)
        return 1

    playlist_name, songs = load_songs(args.playlist)
    print(f"🎧 Playlist: {playlist_name}")
    print(f"🎵 Morceaux: {len(songs)}")

    if args.dry_run:
        for i, song in enumerate(songs, 1):
            print(f"{i:03d}. [{song.section}] {song.artist} - {song.title}")
        return 0

    ensure_music_running()
    ensure_playlist(playlist_name)

    not_found: list[Song] = []
    skipped: list[Song] = []
    current_section = None

    for index, song in enumerate(songs, 1):
        if song.section != current_section:
            current_section = song.section
            print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{current_section}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        label = f"{index:03d}/{len(songs)} {song.artist} - {song.title}"
        if not args.allow_duplicates and playlist_contains(playlist_name, song):
            skipped.append(song)
            print(f"⏭️  {label}")
            continue
        try:
            if add_song(playlist_name, song):
                print(f"✅ {label}")
            else:
                not_found.append(song)
                print(f"❌ {label}")
        except Exception as exc:
            not_found.append(song)
            print(f"⚠️  {label} — {exc}")

    report = write_report(playlist_name, not_found, skipped)
    print("\nTerminé.")
    print(f"✅ Ajoutés potentiels: {len(songs) - len(not_found) - len(skipped)}")
    print(f"⏭️  Déjà présents: {len(skipped)}")
    print(f"❌ Non trouvés: {len(not_found)}")
    print(f"📄 Rapport: {report}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
