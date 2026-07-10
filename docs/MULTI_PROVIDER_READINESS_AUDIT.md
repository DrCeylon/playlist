# Multi-Provider Readiness Audit

**Audience:** maintainers adding Spotify, Deezer, Plex, Jellyfin, Navidrome, Subsonic, SoundCloud, Tidal, Qobuz, Bandcamp, local files, and future providers  
**Date:** July 2026  
**Principle:** YAGNI — remove only assumptions that **block** new providers; no speculative abstractions.

---

## Executive summary

| Layer | Verdict | Notes |
|-------|---------|-------|
| Sync engine (`playlist_sync/`) | ✅ Ready | Provider-neutral; architecture tests enforce no `integration.*` imports |
| Local repository + snapshots | ✅ Ready | SSOT model; immutable `RemotePlaylistSnapshot` |
| Remote playlist read/write ports | ✅ Ready | Capability-gated; YouTube proves second provider |
| Conflict resolution | ✅ Ready | Provider-agnostic kinds |
| Bridge sync commands | ✅ Ready | `plan_sync`, `apply_sync`, `resolve_sync_conflicts` take `provider_id` |
| Streaming import | ⚠️ Was blocked | **Fixed:** `import_port` on gateway; capability-based platform gate |
| Provider listing UI DTO | ⚠️ Was stale | **Fixed:** registry-driven options + planned provider catalog |
| Generation / autocomplete | ⚠️ Apple-only today | Acceptable until second catalog provider ships |
| Swift product UX | ⚠️ Apple-centric | Phase 6.8 — picker, connect UI, manual acquisition copy |
| Closed `ProviderId` enum | ⚠️ By design | Extended with planned IDs; new providers add one enum member |

**Conclusion:** The **hard part** (sync + local SSOT + registry) is multi-provider ready. Remaining work is **per-provider gateway implementation** and **product UX**, not core engine rewrites.

---

## 1. What is already provider-neutral (do not touch)

| Component | Evidence |
|-----------|----------|
| `PlaylistSyncEngine` | No provider imports in `app/playlist_sync/` |
| `PlaylistConflictDetector` / `Resolver` | Kinds: `metadata_mismatch`, `order_mismatch`, … |
| `ManagedPlaylistRepository` | Local JSON SSOT; `LinkedRemoteRef.provider_id` |
| `RemotePlaylistSnapshot` | Immutable; checksum-based archive |
| `ProviderGatewayRegistry` | Open registration at startup |
| `ProviderImportPort` | Frozen protocol — adapters live in `integration/` |
| Bridge contract enum | Commands already include `provider_connect`, `list_remote_playlists`, … |

---

## 2. Implicit assumptions found (by severity)

### Blockers (fixed in this PR)

| Finding | Location | Fix |
|---------|----------|-----|
| `if provider_id == APPLE_MUSIC` for import port | `app/factory.py` | Gateway `import_port` property |
| Hardcoded macOS Apple error in import stream | `import_stream.py` | `gateway.unavailable_reason()` |
| Apple/YouTube `if` in provider options | `provider_platform.py` | Generic auth + `unavailable_reason` |
| Duplicate Apple macOS override in `list_providers` | `backend.py` | Removed — gateway owns platform gate |
| History always tagged `apple_music` on import | `backend._attach_history_import_result` | Pass `provider_id` |
| `IntegrationGateway` reaches into `applescript` | `integration/gateway/service.py` | `prepare_incremental_import()` on import service |

### Friction (documented; implement when needed)

| Finding | Location | When to fix |
|---------|----------|-------------|
| Generation engine always uses Apple catalog | `backend._build_generation_engine` | Second catalog provider |
| Autocomplete empty unless Apple | `autocomplete_search.py` | Second catalog provider |
| Manual acquisition workflow Apple-only | `manual_acquisition_workflow.py` | Second manual-acquire provider |
| `import_playlist` bridge has no `provider_id` param | `commands.py` | Second streaming import provider (optional param) |
| Swift generation hardcodes `.appleMusic` | `PlaylistBuilderViewModel` | Phase 6.8 UX |
| Swift connect/auth commands unused | `BridgeClient` | Phase 6.8 Providers UI |
| `ProviderPlaylistWritePort` no reorder | `playlist_write.py` | Mirror sync production |
| French UI strings reference Music.app | Swift `Support/` | Per-provider deep link abstraction |

### Cosmetic (YAGNI — keep in integration layer)

| Finding | Location |
|---------|----------|
| `persistent_id` in Apple resolver | `integration/apple_music/` |
| `cache/apple_music_identity.json` | `app/settings.py` |
| Theme IDs `apple_music_light` | `ResonanceDesign/` |
| Phase-numbered docs | `docs/product/phase-*` |

---

## 3. Provider taxonomy for future gateways

| Provider type | Auth model | Typical capabilities | Example |
|---------------|------------|----------------------|---------|
| Streaming API | OAuth / API key | catalog, library browse, sync | Spotify, Deezer, Tidal |
| Media server | URL + token / user+pass | library browse, file metadata | Plex, Jellyfin, Navidrome, Subsonic |
| Purchase / indie | Public catalog | public playlist import | Bandcamp |
| Local | None | file scan, local SSOT | `local_files` |
| Experimental | File headers | public import | YouTube Music |

**Rule:** classify by **capabilities**, not by brand. Register only what the gateway actually implements.

---

## 4. `ProviderId` enum policy

`ProviderId` is a closed `StrEnum` — intentional for bridge/DTO stability.

**Extended values (this PR):** `soundcloud`, `tidal`, `qobuz`, `bandcamp`, `plex`, `jellyfin`, `navidrome`, `subsonic`, `local_files`

**Adding a provider:**

1. Add `ProviderId` member + display name in `canonical/provider_ids.py`
2. Mirror in Swift `ProviderID` + `PlaylistLibraryDisplay.providerLabel`
3. Implement `integration/<name>/gateway.py`
4. Register in `app/factory.py`
5. Tests + ADR if auth/write semantics are novel

No stringly-typed provider IDs in persisted data — `parse_provider_id()` rejects unknown values.

---

## 5. Improvements implemented (this PR)

| Change | Justification |
|--------|---------------|
| `AppleMusicProviderGateway.import_port` | Removes factory `if apple` — any gateway can expose import |
| `unavailable_reason()` + `implicit_auth_connected` on Apple gateway | Platform gate lives in integration, not bridge runtime |
| Generic `provider_options_from_registry` | No per-provider `if` in bridge runtime |
| `parse_provider_id()` strict helper | Prevents silent mislabeling as `apple_music` |
| Extended `ProviderId` + display names | Unblocks registration of planned providers |
| `prepare_incremental_import()` on import service | Removes `applescript` leak from generic gateway |
| History `provider_id` on import attach | Correct metadata for multi-provider history |
| Swift enum parity | Bridge/DTO contract alignment |

**Not changed (by design):** `ProviderImportPort`, `PlaylistSyncEngine`, repository contracts, snapshot shape, bridge command enum.

---

## 6. Per-provider readiness checklist

| Provider | Enum | Gateway | Read | Write | Auth | Import stream | Notes |
|----------|------|---------|------|-------|------|---------------|-------|
| Apple Music | ✅ | ✅ | ✅ | ✅ append | implicit macOS | ✅ | Reference impl |
| YouTube Music | ✅ | ✅ | ✅ | ❌ | file headers | ❌ | Experimental |
| Spotify | ✅ | ❌ | ❌ | ❌ | OAuth | ❌ | Next streaming target |
| Deezer | ✅ | ❌ | ❌ | ❌ | OAuth | ❌ | |
| Plex | ✅ | ❌ | ❌ | ❌ | token | ❌ | Media server pattern |
| Jellyfin | ✅ | ❌ | ❌ | ❌ | API key | ❌ | Same as Plex |
| Navidrome | ✅ | ❌ | ❌ | ❌ | Subsonic API | ❌ | Subsonic-compatible |
| Subsonic | ✅ | ❌ | ❌ | ❌ | password+salt | ❌ | |
| SoundCloud | ✅ | ❌ | ❌ | ❌ | OAuth | ❌ | |
| Tidal | ✅ | ❌ | ❌ | ❌ | OAuth | ❌ | |
| Qobuz | ✅ | ❌ | ❌ | ❌ | OAuth | ❌ | |
| Bandcamp | ✅ | ❌ | ❌ | ❌ | public | ❌ | Import-only likely |
| Local files | ✅ | ❌ | ❌ | ❌ | n/a | ❌ | `LOCAL_FILES` + file snapshot path exists |
| Unknown future | add enum | register | ports | ports | optional | optional | Registry pattern |

---

## 7. Architecture diagram

```text
                    ┌─────────────────────────────┐
                    │   ProviderGatewayRegistry    │
                    └─────────────┬───────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
  AppleMusicGateway      YouTubeMusicGateway      (future gateways)
  - import_port          - auth                   - import_port?
  - unavailable_reason   - unavailable_reason     - capabilities
  - playlist_read/write  - playlist_read
         │                        │
         └────────────┬───────────┘
                      ▼
         ┌────────────────────────────┐
         │  Provider-neutral core     │
         │  playlist_sync/            │
         │  playlist_library/         │
         │  canonical/                │
         └────────────────────────────┘
```

---

## 8. Next steps (ordered)

1. **Spotify gateway** — read + OAuth + append_only write (highest user demand)
2. **Swift provider picker** (Phase 6.8) — propagate `provider_id` through generation/import
3. **Provider connect UI** — wire existing bridge `provider_connect` commands
4. **Media server template** — shared Subsonic API adapter for Navidrome/Subsonic; Jellyfin/Plex separate
5. **`local_files` gateway** — scan + metadata; link to existing file snapshot import

---

## References

- [PROVIDER_PLATFORM.md](PROVIDER_PLATFORM.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [ADR-014 — Provider Gateway Architecture](architecture/ADR-014-provider-gateway-architecture.md)
- [ADR-013 — Multi-provider vision](architecture/ADR-013-multi-provider-platform-vision.md)
- Tests: `tests/test_sync_architecture.py`, `tests/test_multi_provider_readiness.py`
