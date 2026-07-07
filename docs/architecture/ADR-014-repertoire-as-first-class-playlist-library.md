# ADR-014 — Répertoire as first-class playlist library

## Status

Proposed — Phase 6 product architecture; **no runtime change** in this ADR.

## Context

Resonance today persists **workflow sessions** (`data/history/sessions.json`) via `SessionHistoryRecord`. The Historique screen serves two incompatible roles:

1. **Technical audit** — generation/import runs, diagnostics, manual-acquisition resume, export.
2. **Pseudo-library** — users replay generation, edit forms, and rediscover playlists from past sessions.

Phase 4.8 explicitly scoped history as a *session log*, not a curated library (`docs/product/phase-4-session-history.md`). As the product evolves toward multi-provider playlist management (ADR-013), a dedicated **Répertoire** domain is required.

ADR-001 established `CanonicalPlaylist` as the provider-neutral musical content model. ADR-011 defined UI layering with ViewModels over bridge contracts. Neither defines a first-class *saved playlist* entity distinct from a workflow session.

## Decision

Introduce **SavedPlaylist** as a first-class Core entity and **Répertoire** as the primary user-facing library screen.

### Domain separation

| Domain | Entity | Purpose | Retention |
|--------|--------|---------|-----------|
| **Répertoire** | `SavedPlaylist` | Curated, user-owned playlist assets | User-controlled delete; independent of workflow |
| **Historique** | `SessionHistoryRecord` | Audit trail of generation/import runs | Technical journal; optional link to `SavedPlaylist` |

### SavedPlaylist ownership

- A `SavedPlaylist` belongs to **Resonance Core** only.
- Content is a `CanonicalPlaylist` plus frozen `PlaylistGenerationRequest` metadata.
- No provider-specific identifiers (`persistent_id`, Spotify URI, etc.) are stored on `SavedPlaylist`.
- `provider_id` on the generation request is **generation context**, not playlist ownership.

### Persistence

- New store: `data/repertoire/playlists.json` (versioned envelope, atomic write — same pattern as session history).
- Optional companion: `data/repertoire/publications.json` (see ADR-015).
- Session history store remains unchanged.

### Navigation

Add `SidebarItem.repertoire` between Nouvelle Playlist and Historique. Répertoire becomes the **primary exploitation screen** for saved playlists.

### Relationship to history

- `SavedPlaylist.originSessionID` optionally links to the creating `SessionHistoryRecord`.
- History does **not** replace Répertoire; migration is additive (see `docs/product/phase-6-repertoire.md`).

## Consequences

### Positive

- Clear product boundary: library vs audit.
- Enables CRUD, filters, merge, and publication without overloading session history.
- Aligns with ADR-013 (Core owns canonical state).

### Trade-offs

- Two persistence stores to maintain (history + répertoire).
- Transitional period where both Historique and Répertoire coexist; edit-from-history must be deprecated gradually.
- One-time migration script may be needed for existing imported sessions.

## Non-goals

- No implementation in this ADR.
- No change to `ProviderImportPort`, manual acquisition workflow (ADR-012), or Phase 5.5 UX.
- No cross-device sync in v1.

## References

- [phase-6-repertoire.md](../product/phase-6-repertoire.md)
- [ADR-001](ADR-001-canonical-model.md)
- [ADR-011](ADR-011-cross-platform-product-ui.md)
- [ADR-013](ADR-013-multi-provider-platform-vision.md)
- [phase-4-session-history.md](../product/phase-4-session-history.md)
