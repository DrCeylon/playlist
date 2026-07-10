# Provider Platform

How Resonance integrates with music services without coupling the core engine to any vendor.

## Core idea

The **engine** manipulates only:

- `RemotePlaylistSnapshot` (immutable remote image)
- `ManagedPlaylistDetail` (local SSOT)
- `PlaylistSyncPlan` / conflicts / operations
- `ProviderId` enum (capability label, not implementation)

**Providers** implement I/O behind ports. The engine never imports Apple Music, YouTube, or Spotify SDKs.

## Registry

```text
ProviderGatewayRegistry
  └── ProviderGateway per ProviderId
        ├── capabilities: frozenset[ProviderCapability]
        ├── catalog (optional)
        ├── library (optional)
        ├── delivery (optional)
        ├── playlist_read (optional)
        ├── playlist_write (optional)
        └── auth (optional)
```

Registration happens at app startup (`app/factory.py`). UI discovers providers via `list_providers` bridge command.

## Capability matrix (current)

| Provider | Catalog | Import stream | Playlist read | Playlist write | Auth |
|----------|---------|---------------|---------------|----------------|------|
| **Apple Music** | ✅ | ✅ | ✅ | ✅ append_only | Implicit (macOS) |
| **YouTube Music** | 🧪 | ❌ | ✅ | ❌ | File headers |
| **Spotify** | 📋 | ❌ | ❌ | ❌ | ❌ |
| **Deezer** | 📋 | ❌ | ❌ | ❌ | ❌ |

## Two service categories (do not mix)

| Category | Examples | Registry |
|----------|----------|----------|
| **Music Providers** | Apple, Spotify, YouTube, Deezer | `ProviderGatewayRegistry` |
| **Resonance Services** (future) | Identity, cloud metadata sync | Separate layer — **not** `ProviderId` |

See [ADR-013](architecture/ADR-013-multi-provider-platform-vision.md).

## Ports (frozen / stable)

| Port | Role |
|------|------|
| `ProviderImportPort` | Stream import to library — **frozen** |
| `ProviderPlaylistReadPort` | List/get remote playlists |
| `ProviderPlaylistWritePort` | Create/update remote playlists |
| `ProviderAuthPort` | Connect/disconnect account |

## Sync engine neutrality

`PlaylistConflictDetector` and `PlaylistConflictResolver` operate on snapshots and local state only. Conflict kinds are provider-agnostic (`metadata_mismatch`, `order_mismatch`, …).

Flow:

```text
plan_sync → conflicts[] (enriched)
resolve_sync_conflicts(resolutions[]) → new plan
apply_sync → ProviderPlaylistWritePort + local repository update
```

## Adding a new provider

1. Create `playlist_builder/integration/<name>/`
2. Implement `ProviderGateway` with explicit `capabilities`
3. Register in factory
4. Add tests (gateway unit + bridge mocks)
5. Add ADR if auth or write semantics are novel
6. Mirror capabilities in Swift `DefaultProviders` for offline UI

**Do not** add provider checks in `app/playlist_sync/` or Swift views.

## Authentication

- Secrets stay on device (Keychain or user file path for experimental YouTube)
- Bridge responses scrubbed via `assert_bridge_safe_mapping`
- See [ADR-015](architecture/ADR-015-provider-auth-boundary.md)

## Experimental providers

YouTube Music is gated behind optional `pip install -e ".[youtube]"`. Gateway registers always; `unavailable_reason` when `ytmusicapi` missing.

Guide: [guides/youtube-music-experimental.md](guides/youtube-music-experimental.md)

## Detailed phase documentation

Implementation history and lot breakdown: [product/phase-6-provider-platform.md](product/phase-6-provider-platform.md)

## Related ADRs

- [ADR-014 — Provider Gateway Architecture](architecture/ADR-014-provider-gateway-architecture.md)
- [ADR-017 — Remote Playlist Snapshot](architecture/ADR-017-remote-playlist-snapshot.md)
- [ADR-018 — Experimental YouTube Music](architecture/ADR-018-experimental-youtube-music-gateway.md)
