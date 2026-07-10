# ADR-022: Layering discipline and future-readiness fixes

**Status:** Accepted  
**Date:** 2026-07-10  
**Context:** [ARCHITECTURE_AUDIT.md](../ARCHITECTURE_AUDIT.md) — Principal Engineer audit pré-v1.0

## Context

Resonance v1.0 ships a modular monolith with strong sync and provider patterns, but structural debt was identified that would compound over 2–3 years:

1. Domain aggregates live under `ui/shared/dto/` while `integration/ports/` import them — inverted layering.
2. `managed_playlists.json` silently wiped data when `schema_version` was newer than supported.
3. `SnapshotArchive.store()` used atomic rename without advisory locking — race under concurrent bridge processes.
4. `get_playlist()` called `list_playlists()` (full sort) on every lookup.
5. No CI guard preventing new layer violations in `integration/ports/`.

This ADR records **accepted fixes** (ROI demonstrated) and **deferred work** (no speculative implementation).

## Decision

### Implemented (v1.0.x)

| Change | Rationale |
|--------|-----------|
| `UnsupportedSchemaVersionError` on newer schema | Prevents silent data loss — real bug class |
| `get_playlist` direct scan without sort | Measurable perf win, zero schema change |
| `SnapshotArchive` immutable publish | `advisory_file_lock` + temp `os.replace` ; mismatch raises explicit error |
| `tests/test_layer_architecture.py` | Prevents regression during domain extraction |
| `ProviderPlaylistWritePort` import in `action_executor` | Fixes static analysis; no behavior change |

### Deferred (requires dedicated epic)

| Item | Trigger to implement |
|------|---------------------|
| Extract `playlist_builder/domain/` | First third-party plugin or SQLite spike |
| Split `RuntimeEngineBridgeBackend` into facades | Bridge command count > 35 or persistent process epic |
| Filter sync plan by `ProviderCapability` | Music.app mirror/reorder validation complete |
| `observability/health` decouple from `AppContext` | Local HTTP API epic |
| SQLite `ManagedPlaylistRepository` backend | User library > 500 playlists or perf regression |

## Consequences

### Positive

- Safer persistence semantics (fail loud on schema mismatch).
- Snapshot store safe under multi-process bridge (current macOS architecture).
- Architecture guards document and enforce transitional boundaries.
- Audit trail for 2.0 planning without code churn.

### Negative / trade-offs

- Apps with newer schema cannot downgrade silently — users must upgrade app (correct behavior).
- Layer guard allows transitional `ui.shared.dto` imports in ports until domain extraction — technical debt remains visible.

## Compliance

- No new features.
- No speculative packages or modules.
- All changes covered by existing + new tests (`test_playlist_repository`, `test_layer_architecture`).

## References

- [ARCHITECTURE_AUDIT.md](../ARCHITECTURE_AUDIT.md)
- [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md)
- [TECHNICAL_DEBT.md](../TECHNICAL_DEBT.md)
- ADR-016 (sync model), ADR-020 (plugin foundations), ADR-013 (multi-provider)
