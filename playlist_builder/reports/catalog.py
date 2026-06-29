from __future__ import annotations

import csv
import html
import urllib.parse
from datetime import datetime
from pathlib import Path

from playlist_builder.core.models import CatalogMatch


def write_catalog_reports(
    playlist_name: str,
    matches: list[CatalogMatch],
    reports_dir: Path,
) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = reports_dir / f"catalog_matches_{stamp}.csv"
    html_path = reports_dir / f"catalog_matches_{stamp}.html"

    rows: list[dict[str, str | int]] = []
    for index, match in enumerate(matches, 1):
        rows.append(
            {
                "index": index,
                "section": match.query.section,
                "artist": match.query.artist,
                "title": match.query.title,
                "matched_artist": match.matched_artist,
                "matched_title": match.matched_title,
                "url": match.url,
                "error": match.error,
            }
        )

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "index",
                "section",
                "artist",
                "title",
                "matched_artist",
                "matched_title",
                "url",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    html_rows: list[str] = []
    for row in rows:
        label = f"{row['index']:03d}. [{row['section']}] {row['artist']} - {row['title']}"
        if row["url"]:
            link = f'<a href="{html.escape(str(row["url"]))}">ouvrir dans Apple Music</a>'
            match_label = f"{row['matched_artist']} - {row['matched_title']}"
        else:
            query = urllib.parse.quote_plus(f"{row['artist']} {row['title']}")
            link = f'<a href="https://music.apple.com/search?term={query}">chercher dans Apple Music</a>'
            match_label = "non trouvé automatiquement"
            if row["error"]:
                match_label = f"{match_label} ({row['error']})"
        html_rows.append(
            "<tr>"
            f"<td>{html.escape(label)}</td>"
            f"<td>{html.escape(str(match_label))}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )

    html_path.write_text(
        f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Apple Music Catalog Matches — {html.escape(playlist_name)}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 40px; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border-bottom: 1px solid #ddd; padding: 8px; text-align: left; }}
tr:hover {{ background: #f7f7f7; }}
</style>
</head>
<body>
<h1>{html.escape(playlist_name)}</h1>
<p>Ouvre les liens pour ajouter les titres à ta bibliothèque Apple Music si le script principal ne les trouve pas.</p>
<table>
<tr><th>Morceau voulu</th><th>Correspondance trouvée</th><th>Action</th></tr>
{chr(10).join(html_rows)}
</table>
</body>
</html>""",
        encoding="utf-8",
    )

    return csv_path, html_path
