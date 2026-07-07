# ADR-017 — Playlist lineage without versioning

## Status

Proposed — Phase 6 product architecture; **no runtime change** in this ADR.

## Context

Phase 6 Répertoire actions include:

- **Modifier** — change generation parameters → produces a **new** playlist.
- **Créer une variation** — copy parameters from an existing playlist → new independent playlist.
- **Fusionner** — combine multiple Répertoire playlists → new playlist.
- **Quelle source d'inspiration !** — AI-inspired generation from an existing playlist → new playlist.

In all cases the **original `SavedPlaylist` remains unchanged**. This is explicitly **not versioning** (no branches, no HEAD, no rollback, no in-place mutation history).

Users may still want **provenance**: knowing which playlist inspired or sourced another. ADR-014 mentions `PlaylistLineage` but does not define semantics.

## Decision

Introduce **`PlaylistLineage`** as optional metadata on `SavedPlaylist` documenting **provenance only**.

### PlaylistLineage structure

| Field | Type | Description |
|-------|------|-------------|
| `kind` | enum | See below |
| `sourcePlaylistIDs` | `[UUID]` | One or more Répertoire playlist IDs |
| `note` | `String?` | Free-text comment (e.g. merge strategy label) |

### Lineage kinds

| Kind | Trigger action | `sourcePlaylistIDs` |
|------|----------------|---------------------|
| `original` | First save after generation (no prior Répertoire source) | `[]` |
| `modifiedFrom` | Modifier (parameters changed, regenerated) | `[sourceID]` |
| `variationOf` | Créer une variation | `[sourceID]` |
| `mergedFrom` | Fusionner | `[id1, id2, …]` |
| `inspiredBy` | Quelle source d'inspiration ! | `[sourceID]` |

### Explicit non-versioning rules

1. **No mutable history chain** — lineage is write-once at creation; not updated when sources are deleted.
2. **No replacement** — modifying playlist A creates playlist B; A is never superseded or marked deprecated.
3. **No merge into existing** — merge always creates a new `SavedPlaylist`.
4. **Deleting a source** does not delete derived playlists; `sourcePlaylistIDs` may become dangling references (UI shows « source supprimée »).
5. **No diff or rollback** — lineage is not a Git-like model.

### UI implications (future)

- Répertoire detail may show « Créée à partir de… » with links to sources when IDs still exist.
- No « version timeline » or « restore previous version » affordances.

## Consequences

### Positive

- Simple mental model: every action creates a new asset.
- Supports audit and discovery without versioning complexity.
- Compatible with AI inspiration flow (future `PlaylistInspirationPort`).

### Trade-offs

- Storage grows with variations; user must delete explicitly.
- Dangling lineage references after source deletion (acceptable; document in UI).

## Non-goals

- Playlist versioning, branching, or collaborative editing.
- Automatic deduplication of similar playlists.
- Implementation in this ADR.

## References

- [phase-6-repertoire.md](../product/phase-6-repertoire.md)
- [ADR-014](ADR-014-repertoire-as-first-class-playlist-library.md)
