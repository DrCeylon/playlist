# ADR-021 — Observability layer foundations

## Status

Accepted

## Context

Resonance already has several observability mechanisms:

- bridge `DiagnosticEvent` stream ;
- opt-in `perf_span` stderr traces ;
- persisted `PlaylistSyncOperation` journal ;
- import diagnostics JSON reports on disk.

Advanced users need a unified, typed view across sync, repository, providers, and system health — without coupling to any single provider SDK. Logs alone are insufficient for timelines, metrics aggregation, and structured export.

## Decision

Introduce `playlist_builder/observability/` as a provider-agnostic in-process layer:

1. **Typed business events** — `ResonanceEvent` + `ResonanceEventKind` + `EventCategory`.
2. **Event bus** — bounded deque, thread-safe, with `get_default_bus()` singleton.
3. **Metrics** — lightweight counters and average durations per event kind.
4. **Recorder** — `ObservabilityRecorder` for sync lifecycle; `NoOpObservabilityRecorder` for tests.
5. **Health** — `build_health_report()` for engine/providers/bus status.
6. **Export** — `export_observability_bundle()` for UI, tests, future API.

Initial integration points (additive only):

- `ApplySyncPlaylist` emits sync apply events.
- `plan_sync()` emits sync plan completed with timing.
- `build_diagnostics_snapshot()` exposes an `observability` section.

`OBSERVABILITY_API_VERSION = "1.0.0"` versions the export contract.

## Constraints

- The observability package MUST NOT import `playlist_builder.integration.*`.
- Existing logs and diagnostics MUST NOT be removed or redirected.
- Provider identifiers are plain strings in events — no `ProviderId` enum dependency in the core package.

## Consequences

Positive:

- Single typed event vocabulary for sync timelines and future surfaces.
- Tests can assert on business events without parsing stderr.
- Diagnostics bridge command gains structured observability payload.

Deferred:

- Provider call tracing (`provider.call`) until a gateway-neutral hook exists.
- Repository/snapshot/generation events until explicit emit points are defined.
- Disk persistence of the event bus (operations journal remains audit SSOT).

## References

- `docs/OBSERVABILITY_ARCHITECTURE.md`
