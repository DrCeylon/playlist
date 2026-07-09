# ADR-017 — Remote Playlist Snapshot

## Status

Accepted — Phase 6.2; extended July 2026 (docs only).

## Context

Comparing and syncing playlists requires an **immutable snapshot** of remote state at a point in time. Live API reads during diff are racy.

Snapshots capture **provider library state** (Music Provider). They are not Resonance Cloud objects — though future Cloud Sync may replicate **references** to local snapshots and managed playlists (metadata only), never re-hosting track audio.

## Decision

### `RemotePlaylistSnapshot`

```python
@dataclass(frozen=True, slots=True)
class RemotePlaylistSnapshot:
    provider_id: ProviderId
    remote_playlist_id: str
    name: str
    snapshot_at_iso: str
    tracks: tuple[RemotePlaylistTrack, ...]
    track_count: int
    checksum: str  # stable hash of track keys + order
    source_kind: str  # provider_library | public_catalog
    source_url: str = ""
```

### Lifecycle

1. **Capture:** `ProviderPlaylistReadPort.get_playlist` → snapshot
2. **Store (optional):** `LocalPlaylistRepository.save_snapshot` for compare offline
3. **Compare:** `PlaylistComparisonService.diff(a, b)` — no provider calls
4. **Import:** snapshot → new `LocalManagedPlaylist` (copy, not reference)

### Swift mirror

`ResonanceCore.RemotePlaylistSnapshot` — same fields, snake_case JSON via `BridgePayloadBuilder`.

### Invariants

- Snapshots are **read-only** value objects
- `remote_track_id` opaque per provider
- Canonical track key for cross-provider compare: normalized `(artist, title)` — not provider IDs

### Open / file sources

Import JSON/CSV produces `RemotePlaylistSnapshot` with:

- `provider_id = YOUTUBE_MUSIC` or dedicated `FILE_IMPORT` pseudo-provider (future enum value) — **or** reuse `publicCatalog` source kind with `provider_id` of target comparison provider

Recommendation v1: `source_kind=public_catalog`, `provider_id` = user-selected comparison target.

## Consequences

- Enables flow D (compare) without live dual API
- Storage growth — prune old snapshots via repository policy (keep last N)

## References

- ADR-016, ADR-018
- `docs/product/phase-6-provider-platform.md`
