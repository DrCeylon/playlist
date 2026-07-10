from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.remote_playlist import (
    RemotePlaylistSnapshot,
    RemotePlaylistTrack,
    remote_playlist_snapshot_checksum,
    utc_now_iso,
)


def load_remote_playlist_snapshot_from_file(
    file_path: Path,
    *,
    provider_id: ProviderId,
    remote_playlist_id: str = "",
    playlist_name: str = "",
    source_kind: str = "public_catalog",
) -> RemotePlaylistSnapshot:
    """Parse a provider-neutral JSON or CSV export into a RemotePlaylistSnapshot."""
    path = file_path.expanduser()
    if not path.exists() or not path.is_file():
        raise ValueError("Fichier playlist introuvable.")

    suffix = path.suffix.lower()
    if suffix == ".json":
        tracks, name = _parse_json_playlist(path.read_text(encoding="utf-8"))
    elif suffix == ".csv":
        tracks, name = _parse_csv_playlist(path)
    else:
        raise ValueError("Format non supporté. Utilisez un export JSON ou CSV.")

    resolved_name = (playlist_name or name or path.stem).strip()
    resolved_id = (remote_playlist_id or f"file:{path.stem}").strip()
    track_tuple = tuple(tracks)
    snapshot_at = utc_now_iso()
    return RemotePlaylistSnapshot(
        provider_id=provider_id,
        remote_playlist_id=resolved_id,
        name=resolved_name,
        snapshot_at_iso=snapshot_at,
        tracks=track_tuple,
        track_count=len(track_tuple),
        checksum=remote_playlist_snapshot_checksum(track_tuple),
        source_kind=source_kind,
        source_url=str(path),
    )


def _parse_json_playlist(raw: str) -> tuple[list[RemotePlaylistTrack], str]:
    payload = json.loads(raw)
    if isinstance(payload, dict) and isinstance(payload.get("tracks"), list):
        playlist_name = str(payload.get("name", "")).strip()
        tracks = [_track_from_mapping(item, index) for index, item in enumerate(payload["tracks"], start=1) if isinstance(item, dict)]
        return tracks, playlist_name
    if isinstance(payload, list):
        tracks = [_track_from_mapping(item, index) for index, item in enumerate(payload, start=1) if isinstance(item, dict)]
        return tracks, ""
    raise ValueError("JSON playlist invalide : attendu un objet avec tracks[] ou une liste de morceaux.")


def _parse_csv_playlist(path: Path) -> tuple[list[RemotePlaylistTrack], str]:
    tracks: list[RemotePlaylistTrack] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV playlist vide.")
        for index, row in enumerate(reader, start=1):
            artist = str(row.get("artist", "")).strip()
            title = str(row.get("title", "")).strip()
            if not artist and not title:
                continue
            tracks.append(
                RemotePlaylistTrack(
                    remote_track_id=str(row.get("remote_track_id", "")).strip() or f"file-track-{index}",
                    artist=artist,
                    title=title,
                    album=str(row.get("album", "")).strip(),
                    duration_ms=int(row.get("duration_ms", 0) or 0),
                    position=int(row.get("position", index) or index),
                )
            )
    return tracks, path.stem


def _track_from_mapping(item: dict[str, Any], position: int) -> RemotePlaylistTrack:
    artist = str(item.get("artist", "")).strip()
    title = str(item.get("title", "")).strip()
    return RemotePlaylistTrack(
        remote_track_id=str(item.get("remote_track_id", "")).strip() or f"file-track-{position}",
        artist=artist,
        title=title,
        album=str(item.get("album", "")).strip(),
        duration_ms=int(item.get("duration_ms", 0) or 0),
        position=int(item.get("position", position) or position),
    )
