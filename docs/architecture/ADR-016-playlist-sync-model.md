# ADR-016 — Playlist Sync Model

## Status

Accepted — Phase 6.4; extended July 2026 for provider vs cloud metadata sync (docs only).

## Context

Phase Playlist Manager introduced:

- `PlaylistSyncDirection`, `PlaylistSyncStatus`, `PlaylistSyncConflict`
- `PlaylistSyncRequest` / `PlaylistSyncResult` (stub)
- `sync_managed_playlist_stub` returning `pending`

We need a **real sync model** that supports dry-run, partial apply, and conflicts without conflating with generation import.

**Terminology:**

| Sync type | Direction | Layer |
|-----------|-----------|-------|
| **Provider sync** | Local ↔ Music Provider (Apple, Spotify, …) | `PlaylistSyncEngine` + read/write ports |
| **Cloud metadata sync** (future) | Mac ↔ Mac via Resonance Cloud Sync | Resonance Services — **not** `ProviderGateway` |

Provider sync never requires a Resonance account. Cloud metadata sync (future) replicates `LocalManagedPlaylist` and related user data — still **no music files**.

## Decision

### Entities

| Entity | Role |
|--------|------|
| `LocalManagedPlaylist` | Resonance-owned playlist (persisted) |
| `RemotePlaylistSnapshot` | Immutable remote image at `snapshot_at` |
| `PlaylistSyncPlan` | Computed diff: actions `add_track`, `remove_track`, `reorder`, `map_track` |
| `PlaylistSyncOperation` | Audited execution of a plan |
| `PlaylistSyncConflict` | Unresolved item blocking auto-apply |

### SyncMode

| Mode | Behaviour |
|------|-----------|
| `dry_run` | Produce plan only |
| `append_only` | Add missing tracks, never remove |
| `mirror` | Destination matches source (dangerous — confirm UI) |
| `manual_resolve` | Stop on first conflict, surface to user |

### Engine flow

```text
1. Load LocalManagedPlaylist + optional RemotePlaylistSnapshot
2. PlaylistSyncEngine.build_plan(direction, mode)
3. PlaylistConflictResolver.validate(plan) → conflicts[]
4. If dry_run OR conflicts with manual_resolve → return plan
5. ProviderPlaylistWritePort / ReadPort apply
6. Persist PlaylistSyncOperation + update LocalManagedPlaylist.sync_status
```

### Bridge mapping

Existing `sync_managed_playlist` evolves to:

```json
{
  "local_playlist_id": "...",
  "direction": "pull_from_provider",
  "provider_id": "apple_music",
  "sync_mode": "dry_run"
}
```

Response includes `sync_plan` when dry-run; `sync_operation` when applied.

### Relation to import

- **Pull** may create/update local playlist — does not call `ProviderImportPort`
- **Push** may use `PlaylistDeliveryPort` internally for Apple track adds — orchestrated by engine, not UI

## Consequences

- Stub `sync_managed_playlist_stub` replaced incrementally behind feature flag
- `ManagedPlaylistSummary` gains optional fields without breaking decode (defaults)

## Non-goals

- Real-time bidirectional sync with music providers
- Automatic conflict resolution in v1
- Storing audio in Resonance cloud
- Modelling Cloud Sync as a music `ProviderId`

## References

- ADR-014, ADR-017
- `PlaylistLibraryModels.swift`, `playlist_library.py`
