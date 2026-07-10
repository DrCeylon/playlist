from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

_PLAYLIST_ID_RE = re.compile(r"^(PL|VL|OLAK5uy_|RD)[\w-]+$", re.IGNORECASE)


def normalize_remote_playlist_id(value: str) -> str:
    """Extract a playlist identifier from a raw id or public URL."""
    raw = value.strip()
    if not raw:
        raise ValueError("remote_playlist_id est requis.")

    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        query = parse_qs(parsed.query)
        list_values = query.get("list") or query.get("playlist")
        if list_values and list_values[0].strip():
            return list_values[0].strip()
        path_parts = [part for part in parsed.path.split("/") if part]
        if path_parts:
            candidate = path_parts[-1]
            if _PLAYLIST_ID_RE.match(candidate):
                return candidate
        raise ValueError("Impossible d'extraire un identifiant de playlist depuis l'URL fournie.")

    if _PLAYLIST_ID_RE.match(raw):
        return raw
    return raw
