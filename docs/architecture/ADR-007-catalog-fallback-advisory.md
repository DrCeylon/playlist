# ADR-007: Catalog fallback advisory on library resolution miss

## Status

Accepted

## Context

PR5 introduced library-scoped resolution via AppleScript. PR6 made failures observable
with query traces and scoring diagnostics. Real E2E tests still returned `NOT_FOUND`
for tracks like `Kygo - Firestone` when the title was absent from the local Music.app
library, even though the iTunes catalog knows the track.

Delivery requires a **library persistent ID**. The catalog cannot directly add tracks
to a playlist without library membership. However, users need actionable guidance when
library resolution fails.

## Decision

When Apple Music library resolution fails, consult the existing `CatalogSearchPort`
(iTunes Search API via `AppleCatalogGateway`) and append an advisory hint:

```text
Catalogue iTunes: Kygo - Firestone (confiance 92). Ajoutez ce morceau à votre bibliothèque Music pour l'importer.
```

Implementation:

| Component | Role |
|-----------|------|
| `catalog_fallback.py` | Builds catalog hints from `CatalogSearchPort` |
| `AppleMusicResolver` | Optional catalog port; enriches `NOT_FOUND` messages |
| `reports/playlist.py` | Persists resolver error text for `NOT_FOUND` rows |

The catalog fallback is **advisory only** — no automatic library import, preserving the
non-destructive philosophy and avoiding AppleScript side effects.

## Consequences

### Positive

- Users understand whether the track is missing from library vs. scoring rejection
- Reuses PR4 catalog gateway inside the Apple provider boundary
- Report files contain full diagnostic text for post-mortem analysis

### Trade-offs

- Extra iTunes API call on library miss (cached via namespaced catalog keys)
- Does not alone fix E2E if the track is not in the local library

### Real E2E requirement

`Kygo - Firestone` must exist in the **local Music.app library** for `ADDED` status.
Catalog fallback explains what to do when it does not.

## Follow-up

- PR8: Application layer reorganization (`app/` bounded context)
- PR9: Wire `ProviderGatewayRegistry` through all entry points
- PR10: Automatic catalog-to-library import (MusicKit or AppleScript) behind explicit opt-in
- PR10: Remove legacy resolver shims
