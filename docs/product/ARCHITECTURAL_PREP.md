# Architectural preparation — immediate actions

**Purpose:** preserve today's codebase so Resonance 2.0 does not require a rewrite.  
**Rule:** no speculative code — only practices and documentation with **immediate utility**.

Parent: [RESONANCE_VISION_2030.md](RESONANCE_VISION_2030.md) · [TARGET_ARCHITECTURE.md](../architecture/TARGET_ARCHITECTURE.md)

---

## What is already future-proof (do not refactor away)

| Asset | 2.0 use | Action today |
|-------|---------|--------------|
| `ManagedPlaylistRepository` | SSOT for rules, undo, multi-sync | Keep as single write path |
| `playlist_version` field | Undo / diff | Increment on every mutation; never remove |
| `RemotePlaylistSnapshot` + archive | Temporal browser | Never mutate stored snapshots |
| `PlaylistSyncOperation` log | Audit + timeline | Append-only; don't truncate |
| `LinkedRemoteRef` | Multi-destination | Allow multiple refs per playlist (already modeled) |
| `PlaylistSyncEngine` | Unchanged core | No provider branches |
| `ProviderGatewayRegistry` | Plugin host precursor | Register gateways only in factory |
| `IdentityCache` | Match feedback | Extend metadata dict, don't new store |
| Bridge command enum | API evolution | ADR before adding commands |
| Architecture guard tests | Regression prevention | Extend when new modules appear |

---

## Immediate practices (starting now)

### 1. Version every local mutation

When changing `ManagedPlaylistDetail`, always bump `playlist_version`. This is **already required** for sync — treat it as mandatory for all repository writes.

**Utility today:** consistent sync conflict detection.  
**Enables 2.0:** undo and diff.

### 2. Never mutate archived snapshots

`snapshot_archive.store()` writes once. If refresh needed, store new checksum.

**Utility today:** deduplication and integrity.  
**Enables 2.0:** point-in-time recovery.

### 3. Log sync operations completely

`PlaylistSyncOperation` must remain the audit source for apply results.

**Utility today:** debugging failed syncs.  
**Enables 2.0:** timeline and compliance export.

### 4. Keep Music Providers ≠ Resonance Services

Do not add `ProviderId.RESONANCE_CLOUD` or similar. Cloud features get a separate namespace when they exist.

**Utility today:** clear mental model (ADR-013).  
**Enables 2030:** optional account without provider coupling.

### 5. Extend DTOs; don't fork parallel models

New product fields (tags, favorites) should extend existing DTOs with optional fields and schema version bumps — not parallel JSON files.

**Utility today:** avoids data fragmentation.  
**Enables 2.0:** single migration path.

### 6. ADR before bridge contract changes

Any new bridge command or breaking JSON field requires ADR + Swift/Python contract tests.

**Utility today:** prevents app/engine drift.  
**Enables 2.0:** local HTTP API can mirror stable contracts.

### 7. YAGNI for new packages

Do **not** create empty `app/rules/`, `app/undo/`, `api/` folders until the epic ships.

**Utility today:** avoids dead code confusion.

---

## Small improvements justified today (documentation only)

This PR delivers documentation only. No runtime changes.

| Deliverable | Immediate utility |
|-------------|-------------------|
| RESONANCE_VISION_2030.md | Aligns all contributors on product direction |
| ROADMAP.md | Prioritization decisions |
| BACKLOG.md | Epic tracking |
| TARGET_ARCHITECTURE.md | Prevents wrong abstractions |
| ADR-019 | Tier boundaries for reviews |
| This document | Checklist for PR reviewers |

---

## PR review checklist (2.0-aware)

When reviewing code, ask:

- [ ] Does this add provider-specific logic outside `integration/`?
- [ ] Does this mutate a stored snapshot?
- [ ] Does this skip `playlist_version` bump?
- [ ] Does this conflate Music Provider with Resonance account?
- [ ] Does this store audio or require cloud to function?
- [ ] Is this building 2.0 infrastructure before 1.0 need? (YAGNI)
- [ ] If bridge contract changes: ADR + Swift tests?

---

## Deferred until tier gate

| Preparation | Earliest tier | Why wait |
|---------------|---------------|----------|
| `app/rules/` package | 2.0 | No second trigger type yet |
| `app/undo/` package | 2.0 | Need mutation log design from real usage |
| Local HTTP API | 2.0 | Bridge sufficient for 1.0 |
| Plugin loader | 2030 | Need 5+ gateways first |
| Resonance Services client | 2030 | No backend |
| MusicBrainz integration module | 2.0 | Enrichment epic |

---

## References

- [TECHNICAL_DEBT.md](../TECHNICAL_DEBT.md)
- [ADR-013](../architecture/ADR-013-multi-provider-platform-vision.md)
- [ADR-016](../architecture/ADR-016-playlist-sync-model.md)
- [ADR-017](../architecture/ADR-017-remote-playlist-snapshot.md)
