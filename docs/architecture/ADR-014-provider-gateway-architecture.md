# ADR-014 — Provider Gateway Architecture (playlist read/write)

## Status

Accepted — Phase 6.1 (contracts); vision extended July 2026 for Resonance Services boundary (docs only).

## Context

ADR-013 defines multi-provider vision. Phase Playlist Manager (tag `phase-playlist-manager-complete`) delivered:

- UI navigation (Playlists, Sync, Providers)
- Bridge commands `list_managed_playlists`, `get_managed_playlist`, `sync_managed_playlist` (stub)
- `ProviderGatewayRegistry` + `ProviderGateway` with catalog/library/delivery ports

**Gap:** no ports to **read or write user playlists** on a provider account. `ProviderImportPort` covers generation→delivery streaming import only and must remain stable (ADR-012).

**Scope boundary:** `ProviderGateway` and `ProviderGatewayRegistry` apply to **Music Providers only**. Resonance Identity, Cloud Sync, AI Profile, Preferences, and Shared Collections are **Resonance Services** — they must not be modelled as `ProviderId` values or registered in the music provider registry (see ADR-013).

## Decision

### Extend `ProviderGateway` (do not replace)

Add optional ports on each provider gateway implementation:

```python
@runtime_checkable
class ProviderPlaylistReadPort(Protocol):
    def list_playlists(self, *, account_id: str | None = None) -> tuple[RemotePlaylist, ...]: ...
    def get_playlist(self, remote_playlist_id: str) -> RemotePlaylistSnapshot: ...

@runtime_checkable
class ProviderPlaylistWritePort(Protocol):
    def create_playlist(self, name: str) -> str: ...  # returns remote_playlist_id
    def upsert_tracks(self, remote_playlist_id: str, tracks: tuple[RemotePlaylistTrack, ...]) -> None: ...
    def remove_tracks(self, remote_playlist_id: str, remote_track_ids: tuple[str, ...]) -> None: ...
```

`ProviderGateway` gains:

```python
@property
def playlist_read(self) -> ProviderPlaylistReadPort | None: ...
@property
def playlist_write(self) -> ProviderPlaylistWritePort | None: ...
```

Capability gating:

- `PLAYLIST_LIBRARY_BROWSE` → read port required for list/get
- `PLAYLIST_SYNC` → write port required for push operations

### Registry (existing)

`ProviderGatewayRegistry` unchanged — register **music** gateways that expose zero or more ports. Future self-hosted libraries (Plex, Jellyfin) follow the same pattern.

### Resonance Services (out of scope)

Cloud Sync of `LocalManagedPlaylist` metadata across Macs is a **Resonance Service**, not a playlist read/write port on a music provider. Do not extend `ProviderGateway` to represent “Resonance Cloud” as a provider.

### Application orchestration

New `PlaylistSyncEngine` in `playlist_builder/app/use_cases/` — **not** inside `import_stream.py`.

### Swift / bridge

New bridge commands (Phase 6.2+):

- `list_remote_playlists`
- `get_remote_playlist`
- `plan_sync` / `apply_sync`

DTOs live in `playlist_builder/ui/shared/dto/` and `ResonanceCore` mirrors.

### Spotify / Deezer (future)

Register stub gateways with empty ports and `is_available=false` — no model changes.

## Consequences

### Positive

- Clear separation: import generation vs library sync
- Apple Music can implement read via Music.app / library APIs without touching `ProviderImportPort`
- Core stays provider-neutral

### Negative

- More ports to mock in tests
- `ProviderGateway` surface grows — document per-provider matrix

## Non-goals

- Modifying `ProviderImportPort` signature
- Cross-provider ID equivalence
- OAuth implementation (see ADR-015)
- Registering Resonance Identity or Cloud Sync as a `ProviderGateway`
- Storing or streaming music via Resonance infrastructure

## Recommendation

Preserve the split between **music integration** (`ProviderGatewayRegistry`) and **user metadata sync** (future Resonance Services). Coupling them would force every provider adapter to understand account state and would erode provider neutrality — the primary architectural advantage of Resonance.

## References

- ADR-013, ADR-012
- `playlist_builder/canonical/contracts.py`
- `docs/product/phase-6-provider-platform.md`
