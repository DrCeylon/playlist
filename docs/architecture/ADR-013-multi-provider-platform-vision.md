# ADR-013 — Multi-provider platform vision (Phase 5.4)

## Status

Proposed — consolidates analysis from Phase 5.4; does not change runtime behaviour.

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
ProviderGatewayRegistry
       ↓
┌──────────────┬──────────────┬──────────────┐
│ Apple Music  │   Spotify    │ YouTube Music│
│ Provider     │   Provider   │   Provider   │
└──────────────┴──────────────┴──────────────┘
       ↓              ↓              ↓
 IdentityCache   IdentityCache   IdentityCache
 (per provider)  (per provider)  (per provider)
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

### Non-goals (Phase 5.4)

- No Spotify or YouTube implementation.
- No change to production acquisition workflow (ADR-012).
- No large refactor — documentation and phased preparation only.

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
