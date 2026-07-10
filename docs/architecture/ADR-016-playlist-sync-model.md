# ADR-016 — Playlist Sync Model

## Status

Accepted — Phase 6.4; **apply layer** added Phase 6.5 (July 2026).

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

### Engine flow (Phase 6.4 — planning)

```text
1. Load LocalManagedPlaylist + optional RemotePlaylistSnapshot
2. PlaylistSyncEngine.build_plan(direction, mode)
3. PlaylistConflictResolver.validate(plan) → conflicts[]
4. If dry_run OR conflicts with manual_resolve → return plan only (no side effects)
```

### Apply flow (Phase 6.5)

```text
1. plan_sync (bridge) — pure; returns plan_checksum
2. apply_sync (bridge) — explicit mutation:
   a. SyncApplyValidator — stale plan/version, destructive confirm, write capability
   b. ApplySyncPlaylist — orchestrator
   c. ProviderPlaylistWritePort / local repository updates
   d. PlaylistSyncStateUpdater — linked_remote_refs (last_seen vs last_applied)
   e. JsonPlaylistSyncOperationRepository — audit trail
```

### Conflict resolution (Phase 6.7)

```text
plan_sync → conflicts[] (enriched, UI-ready)
resolve_sync_conflicts(resolutions[]) → new plan + plan_checksum
apply_sync (only when conflicts cleared or non-manual_resolve)
```

`PlaylistConflictDetector` and `PlaylistConflictResolver` are provider-neutral.
Resolutions: `keep_local`, `keep_remote`, `merge`, `ignore`, `defer`.
Never mutates repository or snapshots — output is always a new plan.

Idempotency key: `local_playlist_id + provider + remote + direction + mode + plan_checksum + versions`.

### Bridge mapping

| Command | Role |
|---------|------|
| `plan_sync` | Dry-run / preview only |
| `apply_sync` | Validated apply (Phase 6.5+) |

Legacy `sync_managed_playlist` remains a stub; use `plan_sync` / `apply_sync`.

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
