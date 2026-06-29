from __future__ import annotations

import csv
import html
import urllib.parse
from datetime import datetime
from pathlib import Path

from playlist_builder.core.models import CatalogMatch


class CatalogReportWriter:
    def __init__(self, reports_dir: Path = Path("reports")) -> None:
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(exist_ok=True)

    def write(self, playlist_name: str, matches: list[CatalogMatch]) -> tuple[Path, Path]:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = self.reports_dir / f"catalog_matches_{stamp}.csv"
        html_path = self.reports_dir / f"catalog_matches_{stamp}.html"
        self._write_csv(csv_path, matches)
        self._write_html(html_path, playlist_name, matches)
        return csv_path, html_path

    def _write_csv(self, path: Path, matches: list[CatalogMatch]) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["index", "section", "artist", "title", "matched_artist", "matched_title", "url", "error"])
            writer.writeheader()
            for index, match in enumerate(matches, 1):
                writer.writerow({
                    "index": index,
                    "section": match.query.section,
                    "artist": match.query.artist,
                    "title": match.query.title,
                    "matched_artist": match.matched_artist,
                    "matched_title": match.matched_title,
                    "url": match.url,
                    "error": match.error,
                })

    def _write_html(self, path: Path, playlist_name: str, matches: list[CatalogMatch]) -> None:
        rows = []
        for index, match in enumerate(matches, 1):
            wanted = f"{index:03d}. [{match.query.section}] {match.query.label}"
            if match.url:
                action = f'<a href="{html.escape(match.url)}">ouvrir dans Apple Music</a>'
                found = f"{match.matched_artist} - {match.matched_title}"
            else:
                query = urllib.parse.quote_plus(match.query.label)
                action = f'<a href="https://music.apple.com/search?term={query}">chercher dans Apple Music</a>'
                found = match.error or "non trouvé automatiquement"
            rows.append(
                "<tr>"
                f"<td>{html.escape(wanted)}</td>"
                f"<td>{html.escape(found)}</td>"
                f"<td>{action}</td>"
                "</tr>"
            )

        path.write_text("""<!doctype html>
<html lang=\"fr\">
<head><meta charset=\"utf-8\"><title>Apple Music Catalog Matches</title>
<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:40px}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:8px;text-align:left}tr:hover{background:#f7f7f7}.ok{color:green}.ko{color:#b00020}</style>
</head><body>
""" + f"<h1>{html.escape(playlist_name)}</h1>" + """
<p>Ouvre les liens pour ajouter les titres à ta bibliothèque Apple Music si le script principal ne les trouve pas.</p>
<table><tr><th>Morceau voulu</th><th>Correspondance trouvée</th><th>Action</th></tr>
""" + "\n".join(rows) + "\n</table></body></html>", encoding="utf-8")
