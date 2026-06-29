#!/usr/bin/env python3
"""
Apple Music catalog checker.

Vérifie les morceaux de la playlist via l'iTunes Search API publique et génère :
- un CSV avec les correspondances trouvées ;
- une page HTML cliquable pour ouvrir chaque morceau dans Apple Music.

Ce script ne modifie pas Apple Music. Il sert à fiabiliser la sélection et à faciliter
l'ajout manuel des morceaux manquants dans ta bibliothèque si nécessaire.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_PLAYLIST = Path("playlists/orlando_pool_party_2026.json")


@dataclass(frozen=True)
class Song:
    artist: str
    title: str
    section: str


def load_songs(path: Path) -> tuple[str, list[Song]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    songs: list[Song] = []
    for section in data.get("sections", []):
        section_name = section.get("name", "Playlist")
        for item in section.get("songs", []):
            songs.append(Song(artist=item["artist"], title=item["title"], section=section_name))
    return data["name"], songs


def search_track(song: Song, country: str, limit: int = 5) -> dict | None:
    term = f"{song.artist} {song.title}"
    query = urllib.parse.urlencode({
        "term": term,
        "country": country,
        "media": "music",
        "entity": "song",
        "limit": str(limit),
    })
    url = f"https://itunes.apple.com/search?{query}"
    with urllib.request.urlopen(url, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    results = data.get("results", [])
    if not results:
        return None

    wanted_artist = song.artist.lower()
    wanted_title = song.title.lower()

    def score(item: dict) -> int:
        artist = item.get("artistName", "").lower()
        title = item.get("trackName", "").lower()
        value = 0
        if wanted_artist == artist:
            value += 50
        elif wanted_artist in artist or artist in wanted_artist:
            value += 30
        if wanted_title == title:
            value += 50
        elif wanted_title in title or title in wanted_title:
            value += 30
        return value

    best = sorted(results, key=score, reverse=True)[0]
    return best if score(best) >= 30 else results[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check tracks against Apple Music/iTunes public catalog.")
    parser.add_argument("--playlist", type=Path, default=DEFAULT_PLAYLIST)
    parser.add_argument("--country", default="us", help="Store country, e.g. us, ch, fr. Default: us")
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between API calls")
    args = parser.parse_args()

    if not args.playlist.exists():
        print(f"Fichier introuvable: {args.playlist}", file=sys.stderr)
        return 1

    playlist_name, songs = load_songs(args.playlist)
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = reports / f"catalog_matches_{stamp}.csv"
    html_path = reports / f"catalog_matches_{stamp}.html"

    rows: list[dict] = []
    print(f"🎧 {playlist_name}")
    print(f"🔎 Vérification catalogue Apple/iTunes: {len(songs)} morceaux")

    for index, song in enumerate(songs, 1):
        try:
            match = search_track(song, args.country)
        except Exception as exc:
            match = None
            print(f"⚠️  {index:03d}/{len(songs)} {song.artist} - {song.title}: {exc}")

        if match:
            print(f"✅ {index:03d}/{len(songs)} {song.artist} - {song.title}")
            rows.append({
                "index": index,
                "section": song.section,
                "artist": song.artist,
                "title": song.title,
                "matched_artist": match.get("artistName", ""),
                "matched_title": match.get("trackName", ""),
                "url": match.get("trackViewUrl", ""),
            })
        else:
            print(f"❌ {index:03d}/{len(songs)} {song.artist} - {song.title}")
            rows.append({
                "index": index,
                "section": song.section,
                "artist": song.artist,
                "title": song.title,
                "matched_artist": "",
                "matched_title": "",
                "url": "",
            })
        time.sleep(args.sleep)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "section", "artist", "title", "matched_artist", "matched_title", "url"])
        writer.writeheader()
        writer.writerows(rows)

    html_rows = []
    for row in rows:
        label = f"{row['index']:03d}. [{row['section']}] {row['artist']} - {row['title']}"
        if row["url"]:
            link = f'<a href="{html.escape(row["url"])}">ouvrir dans Apple Music</a>'
            match_label = f"{row['matched_artist']} - {row['matched_title']}"
        else:
            query = urllib.parse.quote_plus(f"{row['artist']} {row['title']}")
            link = f'<a href="https://music.apple.com/search?term={query}">chercher dans Apple Music</a>'
            match_label = "non trouvé automatiquement"
        html_rows.append(f"<tr><td>{html.escape(label)}</td><td>{html.escape(match_label)}</td><td>{link}</td></tr>")

    html_path.write_text("""<!doctype html>
<html lang=\"fr\">
<head><meta charset=\"utf-8\"><title>Apple Music Catalog Matches</title>
<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:40px}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:8px;text-align:left}tr:hover{background:#f7f7f7}</style>
</head><body>
<h1>Apple Music Catalog Matches</h1>
<p>Ouvre les liens pour ajouter les titres à ta bibliothèque Apple Music si le script principal ne les trouve pas.</p>
<table><tr><th>Morceau voulu</th><th>Correspondance trouvée</th><th>Action</th></tr>
""" + "\n".join(html_rows) + "\n</table></body></html>", encoding="utf-8")

    found = sum(1 for r in rows if r["url"])
    print("\nTerminé.")
    print(f"✅ Correspondances catalogue: {found}/{len(rows)}")
    print(f"📄 CSV: {csv_path}")
    print(f"🌐 HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
