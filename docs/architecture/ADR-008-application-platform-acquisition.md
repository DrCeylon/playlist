# ADR-008: Application platform foundation and catalog-to-library acquisition

## Status

Accepted

## Context

PR5–PR7 established delivery, observable resolution, and catalog advisory. Real E2E
for `Kygo - Firestone` showed:

- iTunes catalog finds the track (80% confidence, feat. Conrad Sewell variant)
- Music.app local library returns zero candidates
- Advisory-only fallback cannot produce `ADDED`

CLI entry points still bypassed a unified application layer. Incremental import
dropped resolver diagnostics. Scoring used inconsistent normalization between
catalog and fuzzy resolution paths.

## Decision

### 1. Application layer (`playlist_builder/app/`)

Introduce a composition root and use cases:

| Component | Role |
|-----------|------|
| `AppSettings` | Central runtime configuration |
| `AppContext` / `build_app_context()` | Composition root |
| `ImportPlaylistUseCase` | Sync/incremental import via `IntegrationGateway` |
| `CheckCatalogUseCase` | Catalog verification via provider gateway |

CLIs become thin shells delegating to use cases.

### 2. Catalog-to-library acquisition (opt-out)

> **Amendment (Phase 5.4):** Production automatic acquisition is governed by
> [ADR-012](ADR-012-apple-catalog-acquisition-production-policy.md) (S1 quick probe
> + manual gate). The S2 open/play/duplicate path below is **deprecated for production**
> and retained only as `LEGACY_EXPERIMENTAL`.

When library search returns no acceptable candidates and iTunes catalog confidence
≥ 70, attempt to add the track URL to Music.app via AppleScript (`add` then `open location`
fallback), re-search the library, then score and deliver.

Controlled by `AppSettings.acquire_missing_from_catalog` (default **True**).
Disable with `--no-acquire` on `create_playlist.py`.

Non-destructive: never deletes playlists; only adds missing tracks to library when enabled.

### 3. Scoring alignment

`score_text_match()` now uses `normalize_text()` on both sides, stripping `feat.` /
`featuring` suffixes consistently with fuzzy resolution.

### 4. Diagnostics

- JSON import diagnostics (`reports/import_diagnostics_*.json`) via `--json-diagnostics`
- Resolver traces include `catalog_acquired` flag
- Text reports include full `NOT_FOUND` error messages

## Consequences

### Positive

- E2E path can succeed when catalog URL acquisition works on macOS Music.app
- Single gateway routing for sync and incremental import
- Application layer ready for future UI without CLI coupling
- AAA-scale separation: App → Gateway → Provider

### Trade-offs

- AppleScript `add URL` behavior varies by macOS / Music.app version
- Automatic library acquisition requires explicit opt-out (`--no-acquire`)
- MusicKit auto-import remains a separate experimental engine

## Follow-up

- PR9: Wire `generate_playlist.py` through `AppContext`
- PR10: Generic `ResolutionTrace` contract for multi-provider diagnostics
- PR10: Remove legacy `resolver/applescript.py` and scoring facades
- Optional MusicKit acquisition behind same `LibraryAcquisitionPort`
