# ADR-016 — Playlist export formats

## Status

Proposed — Phase 6 product architecture; **no runtime change** in this ADR.

## Context

ADR-014 introduces `SavedPlaylist` as Core-owned canonical content in the Répertoire. Users will need to **export** playlists without involving a streaming provider — for backup, sharing, or use in external tools.

ADR-013 positions providers as delivery destinations. **File export** is neither generation nor provider publication; it is a **read-only projection** of `CanonicalPlaylist` into portable formats.

Today, Resonance can export **session metadata** (`export_history_session`) but not a first-class playlist library artifact in standard interchange formats.

## Decision

Introduce **PlaylistExportPort** as a provider-neutral application port that projects `CanonicalPlaylist` (from `SavedPlaylist`) into file formats **without altering the source model**.

### Supported formats (roadmap)

| Format | MIME / extension | Primary use |
|--------|------------------|-------------|
| **M3U** | `audio/x-mpegurl`, `.m3u` | Universal playlist interchange |
| **CSV** | `text/csv`, `.csv` | Spreadsheets, analysis |
| **JSON** | `application/json`, `.json` | Resonance interchange, tooling |

### Export request model

```text
ExportPlaylistRequest
├── playlistID: UUID
├── format: m3u | csv | json
└── destinationPath: String?   // optional; default to user-selected path via UI
```

### Projection rules

- Export reads `SavedPlaylist.playlist` (`CanonicalPlaylist`) only.
- Output contains **canonical fields** (artist, title, section, duration when known).
- Provider-specific IDs are **omitted** from default export formats (optional extension field in JSON only, namespaced).
- Export does **not** create a `PlaylistPublication` record (no provider involved).

### PlaylistExportPort

```text
export(playlist: SavedPlaylist, format: ExportFormat) -> ExportResult
```

Bridge command (future): `export_repertoire_playlist`.

### UI

Triggered from Répertoire detail action bar. No change to Nouvelle Playlist or live import UX in Phase 6.0.

## Consequences

### Positive

- Provider-independent exit path aligned with ADR-001.
- Adding a new format requires only a new projector, not model changes.
- JSON export enables future import-into-Répertoire tooling (out of scope here).

### Trade-offs

- M3U lacks rich metadata (sections, scores); CSV/JSON carry more structure.
- File writes are local-only; no cloud sync in v1.

## Non-goals

- Import from M3U/CSV into Répertoire (future ADR if needed).
- Embedded provider deep links in M3U.
- Implementation in this ADR.

## References

- [phase-6-repertoire.md](../product/phase-6-repertoire.md)
- [ADR-014](ADR-014-repertoire-as-first-class-playlist-library.md)
- [ADR-001](ADR-001-canonical-model.md)
