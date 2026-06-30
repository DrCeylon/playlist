# ADR-010 — Phases 2 and 3 completion

## Status

Accepted

## Context

Phases 2 and 3 established the target architecture:

- canonical model in `playlist_builder/canonical/`
- generic integration gateway in `playlist_builder/integration/gateway/`
- Apple Music isolated in `playlist_builder/integration/apple_music/`
- `IdentityCache` for provider-neutral → provider-specific mappings

Before this ADR, several application paths still reached Apple Music directly:

- incremental CLI preparation called `AppleScriptClient` from `create_playlist.py`
- `ImportPlaylistUseCase` bypassed the gateway for incremental imports
- `CheckCatalogUseCase` used `context.apple_music.catalog`
- `ResolutionCandidate` exposed `persistent_id` in the scoring layer

## Decision

Complete phases 2 and 3 without a big-bang rewrite:

1. Route **all** playlist imports through `IntegrationGateway.import_playlist()`.
2. Add gateway helpers:
   - `prepare_incremental_import()` for incremental CLI orchestration
   - `search_catalog()` for catalog checks
   - `flush_caches()` for identity and catalog persistence
3. Keep `create_playlist.py` as CLI orchestration only.
4. Rename `ResolutionCandidate.persistent_id` to `provider_key` in `scoring/`.
5. Remove dead legacy code `resolver/applescript.py`.
6. Document the real Apple Music E2E flow in `docs/e2e-apple-gateway.md`.

Provider-specific identifiers (`persistent_id`, AppleScript, MusicKit) remain confined to `integration/apple_music/`.

## Consequences

Positive:

- Core layers (`canonical/`, `app/`, `scoring/`, `planning/`) stay provider-neutral.
- New providers can register in `ProviderGatewayRegistry` without touching use cases.
- Incremental and sync imports share one integration path.
- Tests cover gateway routing, CLI flags, and mocked acquisition flows.

Trade-offs:

- `AppContext.apple_music` remains as a test/extension accessor; use cases must not depend on it.
- `MusicClient` and `resolver/*` facades remain as legacy shims until PR 10.

## Related documents

- [ADR-008](ADR-008-application-platform-acquisition.md)
- [ADR-009](ADR-009-apple-catalog-acquisition-workflow.md)
- [E2E Apple Gateway](../e2e-apple-gateway.md)
