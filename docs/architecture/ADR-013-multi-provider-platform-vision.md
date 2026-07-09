# ADR-013 — Multi-provider platform vision (Phase 5.4)

## Status

Accepted — consolidates analysis from Phase 5.4; extended July 2026 for Resonance Identity vision (docs only). Does not change runtime behaviour.

## Context

Phases 5.3.1–5.3.4 established that:

- The Python bridge and Apple delivery are no longer import bottlenecks.
- `IdentityCache` (PID) provides a fast, reliable resolution path.
- AppleScript automatic acquisition (S2) is structurally limited; production uses S1 + manual S4 (ADR-012).
- Resonance must evolve from an Apple Music client into a **provider-neutral playlist engine**.

The canonical layer (`canonical/`, ADR-001) and gateway pattern (ADR-010) were designed for multi-provider, but **runtime wiring remains Apple-centric** — especially `app/bridge_runtime/import_stream.py` and duck-typed `applescript` access in `IntegrationGateway`.

## Decision

### Product positioning

Resonance Core owns **composition** and **canonical playlist state**. Providers own **resolution, acquisition, delivery, and external ID persistence**. The UI and bridge manipulate canonical identities and provider-agnostic import states — never Apple `persistent_id` or Spotify URI in shared contracts.

**Resonance Identity is not a music provider.** A future optional Resonance account (Identity, Cloud Sync, AI Profile, Preferences, Shared Collections) lives in a **separate service layer** that synchronizes user metadata across devices — never audio, never provider OAuth tokens, and never registered in `ProviderGatewayRegistry`.

### Two service categories

| Category | Examples | Registry / ports |
|----------|----------|------------------|
| **Music Providers** | Apple Music, Spotify, YouTube Music, Deezer, Plex, Jellyfin | `ProviderGatewayRegistry`, `ProviderGateway`, `ProviderImportPort`, playlist read/write ports |
| **Resonance Services** | Identity, Cloud Sync, AI Profile, Preferences, Shared Collections | Future dedicated layer — **not** `ProviderId`, **not** `ProviderGateway` |

### Architecture principles (local-first & optional account)

- **Local operation is the reference** — all features work without a Resonance account.
- **Resonance account is entirely optional** — no gate on generation, import, or provider sync.
- **Music providers remain independent** — each OAuth secret stays in local Keychain; no central Resonance OAuth broker in Phase 6.
- **Cloud sync is metadata-only** — managed playlists, exclusions, preferences, AI profiles — **no music files** stored by Resonance.
- **Never conflate** Music Provider auth (`ProviderAuthPort`) with Resonance Identity login (future ADR).

**Recommendation:** maintain this separation of responsibilities to avoid coupling the Resonance platform to any single music vendor. This is a **major competitive advantage**: users keep local control and provider choice while optionally gaining cross-device metadata sync.

### Target architecture

```text
UI / CLI / Bridge
       ↓
Application (use cases — provider-neutral)
       ↓
Canonical model + ports (CatalogSearchPort, LibraryResolvePort,
                         PlaylistDeliveryPort, ProviderImportPort*)
       ↓
IntegrationGateway (orchestration only — no AppleScript)
       ↓
ProviderGatewayRegistry          ← Music Providers ONLY
       ↓
┌──────────────┬──────────────┬──────────────┐
│ Apple Music  │   Spotify    │ YouTube Music│
│ Provider     │   Provider   │   Provider   │
└──────────────┴──────────────┴──────────────┘
       ↓              ↓              ↓
 IdentityCache   IdentityCache   IdentityCache
 (per provider)  (per provider)  (per provider)

        ═══════════════════════════════════════
        Future (separate layer — NOT providers):

┌─────────────────────────────────────────────┐
│ Resonance Services (optional account)        │
│ Identity · Cloud Sync · AI Profile · Prefs   │
│ Shared Collections — metadata sync only      │
└─────────────────────────────────────────────┘
```

`*` `ProviderImportPort` — new port for streaming import events and manual acquisition (not yet extracted; today lives in `import_stream.py`).

### Identity model

Keep `IdentityCache` as the persistence primitive. Introduce a **ProviderIdentityRegistry** façade (future) that:

- Exposes `get(track, provider_id) → ProviderIdentity | None`
- Allows **one external_id per (canonical_key, provider_id)** — sufficient for delivery
- Does **not** attempt cross-provider ID equivalence in v1 (no “this Apple PID = this Spotify URI”)
- Optional future: `metadata` on `ProviderIdentity` for acquisition state (`pending`, `manual_required`)

### What stays Apple-local (ADR scope)

| Concern | ADR owner |
|---------|-----------|
| Catalog search (iTunes API) | ADR-004 |
| Delivery (AppleScript batch) | ADR-005 |
| Resolution diagnostics | ADR-006 |
| Catalog fallback advisory | ADR-007 |
| App composition | ADR-008 |
| Acquisition workflow history | ADR-009 (partial), **ADR-012 (production)** |
| Gateway unification | ADR-010 |
| Product UI / bridge | ADR-011 |

New providers require **provider-local ADRs** (e.g. ADR-014 Spotify acquisition, ADR-015 YouTube delivery).

### Non-goals (Phase 5.4 / Phase 6 docs)

- No Spotify or YouTube implementation (in early phases).
- No change to production acquisition workflow (ADR-012).
- No large refactor — documentation and phased preparation only.
- **No Resonance Identity backend, user accounts, or cloud API** — documented as future Resonance Services only.

### Long-term vision enabled by this architecture

When Resonance Services are implemented (post-Phase 6), the same boundaries enable:

- Multi-Mac sync of managed playlists and exclusions
- Cross-device AI generation preferences
- Multi-provider search and cross-platform playlist comparison (via existing provider layer)
- Shared collections and family collaboration on **metadata**
- Marketplace of generation rules and templates — **not music hosting**

## Consequences

### Positive

- Clear boundary for future PRs: bridge must not import `integration.apple_music`.
- IdentityCache model already supports N providers without schema change.
- Small-commit roadmap can proceed without breaking Resonance macOS.

### Trade-offs

- Short-term duplication: bridge import path parallel to `IntegrationGateway.import_playlist`.
- `ProviderImportPort` extraction deferred — acceptable until second provider needs streaming import.
- Cross-provider “open in Spotify if not on Apple” requires future product ADR, not technical cache alone.

## Implementation roadmap

See `wiki/Phase-5-4-Architecture-Consolidation.md` § Roadmap.

## References

- `docs/architecture/vision.md`
- `wiki/Phase-5-3-3-Acquisition-Decision.md`
- `wiki/Phase-5-4-Architecture-Consolidation.md`
