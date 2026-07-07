# ADR-015 — Playlist publication as provider destination

## Status

Proposed — Phase 6 product architecture; **no runtime change** in this ADR.

## Context

Today, the only path from a generated playlist to a provider is the **live import workflow**: Nouvelle Playlist → Aperçu → `import_playlist_stream` → Apple Music delivery. The import result is attached to a `SessionHistoryRecord`.

ADR-013 states: *Resonance Core owns composition and canonical playlist state; providers own resolution, acquisition, delivery, and external ID persistence.*

Phase 6 introduces a **Répertoire** of saved playlists (ADR-014). Users must be able to **publish** a saved playlist to a connected provider **without modifying** its Core content first. This is distinct from:

- **Generation** — creating new canonical content.
- **Import (live workflow)** — streaming import during or immediately after generation.
- **Export** — file projection (ADR-016).

`ProviderImportPort` (Phase 5.5) handles streaming import events and manual acquisition for Apple Music. It must **not** be modified to absorb Répertoire concerns; publication should compose it (or future delivery ports) from a separate use case.

## Decision

Model **publication** as a separate concern from **playlist ownership**, via `PlaylistPublication`.

### PlaylistPublication entity

Stored in `data/repertoire/publications.json`, separate from `SavedPlaylist`:

| Field | Role |
|-------|------|
| `playlistID` | References `SavedPlaylist.id` |
| `providerID` | Destination provider |
| `publishedAt` | Timestamp |
| `status` | `published` \| `partial` \| `failed` |
| `externalReference` | Opaque provider-side ID (never embedded in `SavedPlaylist`) |
| `importSessionID` | Optional link to `SessionHistoryRecord` for this publish run |

One `SavedPlaylist` may have **multiple** `PlaylistPublication` records (e.g. Apple today, Spotify tomorrow).

### PlaylistPublicationPort

New application port (future):

```text
publish(playlist: SavedPlaylist, provider_id: ProviderId) -> AsyncStream<PublicationEvent>
```

Implementation may delegate resolution and delivery to existing provider infrastructure (`ProviderImportPort`, `PlaylistDeliveryPort`) but the **orchestration and UI** are Répertoire-specific.

### Rules

1. Publishing **never mutates** `SavedPlaylist` content or generation parameters.
2. Provider IDs are recorded only on `PlaylistPublication`, not on `SavedPlaylist`.
3. Publication runs create an **audit entry** in session history (technical journal) but history does not own the playlist.
4. Manual acquisition during publish-from-Répertoire reuses the existing workflow coordinator; ADR-012 policy unchanged.

### UI

`PlaylistPublicationViewModel` (dedicated) — not merged into `ImportViewModel` — to avoid conflating live creation import with library publication.

Bridge command (future): `publish_repertoire_playlist`.

## Consequences

### Positive

- Clean multi-provider story: same Core playlist → N provider destinations.
- External IDs isolated from canonical model (ADR-001, ADR-013).
- Publication history visible per playlist in Répertoire detail.

### Trade-offs

- Additional persistence file and port abstraction.
- Some overlap with live import event streaming; shared event DTOs may be reused but use cases stay separate.

## Non-goals

- No Spotify/YouTube implementation in this ADR.
- No modification to `ProviderImportPort` signature or manual acquisition state machine.
- No automatic publish-on-save.

## References

- [phase-6-repertoire.md](../product/phase-6-repertoire.md)
- [ADR-014](ADR-014-repertoire-as-first-class-playlist-library.md)
- [ADR-013](ADR-013-multi-provider-platform-vision.md)
- [ADR-012](ADR-012-apple-catalog-acquisition-production-policy.md)
