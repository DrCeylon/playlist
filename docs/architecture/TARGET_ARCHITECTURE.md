# Target architecture — Resonance 2.0

**Status:** target state (not fully implemented)  
**Parent:** [RESONANCE_VISION_2030.md](../product/RESONANCE_VISION_2030.md) · [ADR-019](ADR-019-resonance-product-tiers.md)

Describes where the **technical** architecture must evolve to support 2.0 without rewrites.

---

## Current → target

```text
TODAY (MVP)                          TARGET (2.0)
─────────────                        ─────────────

Composition engine                   + Rules engine (local evaluator)
  └─ scoring                           └─ triggers → actions on SSOT

ManagedPlaylistRepository (SSOT)     + Tag index, favorites store
  └─ playlist_version                  + Undo stack / mutation log
  └─ snapshot archive                  + Temporal index (by date)

PlaylistSyncEngine                   + Multi-target orchestrator
  └─ plan / apply / conflicts            └─ N LinkedRemoteRef per playlist
                                         └─ Scheduled job runner (local)

ProviderGatewayRegistry              + Plugin registry (gateways)
  └─ 2 gateways                        └─ 5+ gateways + community plugins

Bridge JSON-RPC                      + Local HTTP API (read/write library)
  └─ macOS app                         └─ Shortcuts / HA / CLI consumers

History sessions                     + Unified audit log (all mutations)

IdentityCache (per provider)         + Match feedback store
                                       + MusicBrainz reference layer
```

---

## Layering (unchanged principle)

Dependencies point **inward**. New 2.0 modules follow the same rule:

```text
┌─────────────────────────────────────────────────────────────┐
│ Surfaces: macOS · iOS · CLI · Shortcuts · HTTP API · HA      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│ Application use cases                                        │
│  generation · import · sync · rules · undo · schedule        │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│ Domain (provider-neutral)                                    │
│  canonical/ · playlist_library/ · playlist_sync/           │
│  rules/ (future) · audit/ (future)                         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│ Ports & registry                                             │
│  ProviderGatewayRegistry · PluginRegistry (future)           │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│ Integration (provider-specific)                              │
│  apple_music/ · spotify/ · plex/ · …                       │
└─────────────────────────────────────────────────────────────┘

        ═══════════════════════════════════════════════════
        Separate (optional, metadata only):

┌─────────────────────────────────────────────────────────────┐
│ Resonance Services — NOT in ProviderGatewayRegistry          │
│  Identity · Cloud Sync · Shared Collections · AI Profile     │
└─────────────────────────────────────────────────────────────┘
```

---

## Core domain objects (evolution)

| Object | Today | 2.0 extension |
|--------|-------|---------------|
| `ManagedPlaylistDetail` | SSOT + version | + tags, collection_id, rule_ids |
| `ManagedPlaylistTrack` | position, identity | + user_tags, favorite_flag, match_confidence |
| `LinkedRemoteRef` | 1:1 provider link | N refs per local playlist |
| `RemotePlaylistSnapshot` | immutable point-in-time | indexed by `captured_at` |
| `PlaylistSyncOperation` | audit log entry | source for undo + timeline |
| `PlaylistSyncConflict` | resolution choices | + AI suggestion metadata (optional) |
| `IdentityCache` | provider external_id | + user_feedback, mbid, isrc refs |

**Rule:** extend via new fields and sibling modules — do not replace SSOT or snapshot contracts.

---

## New modules (2.0 — planned, not speculative today)

| Module | Responsibility | Depends on |
|--------|----------------|------------|
| `app/rules/` | Evaluate declarative rules locally | SSOT, generation, sync |
| `app/schedule/` | Cron-like local job runner | rules, sync |
| `app/undo/` | Mutation log + rollback | repository, audit log |
| `app/library_index/` | Cross-playlist search, tags | SSOT |
| `app/enrichment/` | MusicBrainz / ISRC lookups | canonical, cache |
| `integration/plugins/` | Load third-party gateways | registry |
| `api/local/` | HTTP server (localhost) | bridge or direct use cases |

**None of these exist yet.** Folders should be created only when the first epic ships (YAGNI).

---

## Rules engine (target design)

```text
Rule = Trigger + Condition[] + Action[]

Triggers (2.0):
  - schedule(cron)
  - catalog.new_release(artist)
  - webhook(path)
  - manual

Conditions:
  - playlist.tags contains X
  - track.genre matches Y
  - provider.capability Z

Actions:
  - playlist.add_tracks(from: generation | catalog | playlist)
  - playlist.remove_tracks(where: …)
  - sync.push(provider_id)
  - sync.pull(provider_id)
```

Rules mutate **local SSOT first**; sync is always a separate explicit action (or chained action invoking existing `plan_sync` / `apply_sync`).

---

## Undo & versioning (target design)

Building on existing `playlist_version`:

```text
MutationLog (append-only)
  - mutation_id
  - local_playlist_id
  - playlist_version_before / after
  - operation_kind (add_tracks | remove | reorder | sync_apply | rule_action)
  - reversible_payload (JSON)
  - timestamp

Undo:
  - pop last reversible mutation
  - restore ManagedPlaylistDetail from payload OR decrement version
  - does NOT auto-revert provider (user triggers sync)
```

**Foundation already in repo:** `playlist_version`, `PlaylistSyncOperation`, snapshot archive.

---

## Multi-destination sync (target design)

```text
ManagedPlaylistDetail
  linked_remote_refs: [
    { provider: apple_music, remote_id: … },
    { provider: spotify, remote_id: … },
  ]

Sync orchestrator:
  for each ref in refs:
    plan = engine.plan(local, snapshot_for(ref), ref.provider)
    if conflicts: surface batch
    apply(plan, ref.provider)
```

No change to `PlaylistSyncEngine` per-provider logic — only orchestration layer above.

---

## API surfaces (target)

| Surface | Tier | Scope |
|---------|------|-------|
| Bridge JSON-RPC | MVP ✅ | App ↔ engine |
| CLI | MVP ✅ | Automation |
| Local HTTP API | 2.0 | `localhost:PORT/v1/library/...` |
| Public HTTP API | 2030 | Authenticated; metadata only |
| Plugin manifest | 2030 | `resonance-plugin.json` |

---

## Architectural guardrails (do not break)

| Guardrail | Why |
|-----------|-----|
| No audio bytes in Resonance storage | Legal, scope, trust |
| Music Providers ≠ Resonance Services | ADR-013 |
| `playlist_sync/` stays provider-blind | Tested by arch guards |
| Snapshots immutable once written | Time-travel depends on this |
| Bridge contract changes need ADR + Swift parity | Multi-surface consumers |
| `ProviderImportPort` frozen until second import provider needs extension | YAGNI |
| Rules never call provider SDKs directly | Always through ports |

---

## Migration path (no big bang)

| Phase | Technical work |
|-------|----------------|
| MVP → 1.0 | More gateways; UX; no new domain modules |
| 1.0 → 2.0 | Add `rules/`, `undo/`, `schedule/` incrementally |
| 2.0 → 2030 | Plugin host, public API, Resonance Services |

Each increment keeps `main` deployable.

---

## References

- [vision.md](vision.md) — original engineering vision
- [ADR-013](ADR-013-multi-provider-platform-vision.md) — provider platform
- [ADR-016](ADR-016-playlist-sync-model.md) — sync model
- [ADR-017](ADR-017-remote-playlist-snapshot.md) — snapshots
- [ARCHITECTURAL_PREP.md](../product/ARCHITECTURAL_PREP.md) — what to do now
