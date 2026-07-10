# Architecture

This directory contains the long-lived architectural documentation for **Resonance** (Python package: `playlist-builder`).

**Start here:** [../ARCHITECTURE.md](../ARCHITECTURE.md) — hub linking ADRs, modules, and invariants.

## Documents

| Document | Purpose |
|----------|---------|
| [vision.md](vision.md) | Target platform architecture and bounded contexts |
| [ADR-001-canonical-model.md](ADR-001-canonical-model.md) | Canonical domain model decision record |
| [ADR-002-unified-scoring.md](ADR-002-unified-scoring.md) | Unified scoring engine decision record |
| [ADR-003-identity-cache.md](ADR-003-identity-cache.md) | Cross-provider identity cache decision record |
| [ADR-004-apple-catalog-gateway.md](ADR-004-apple-catalog-gateway.md) | Apple catalog provider gateway decision record |
| [ADR-005-apple-delivery-gateway.md](ADR-005-apple-delivery-gateway.md) | Apple delivery + identity-cache resolution decision record |
| [ADR-006-observable-resolution-pipeline.md](ADR-006-observable-resolution-pipeline.md) | Observable Apple Music resolution diagnostics decision record |
| [ADR-007-catalog-fallback-advisory.md](ADR-007-catalog-fallback-advisory.md) | Catalog fallback advisory on library miss decision record |
| [ADR-008-application-platform-acquisition.md](ADR-008-application-platform-acquisition.md) | Application layer and catalog-to-library acquisition decision record |
| [ADR-009-apple-catalog-acquisition-workflow.md](ADR-009-apple-catalog-acquisition-workflow.md) | Apple catalog acquisition workflow decision record |
| [ADR-010-phases-2-3-completion.md](ADR-010-phases-2-3-completion.md) | Phases 2 and 3 enterprise architecture completion |
| [ADR-011-cross-platform-product-ui.md](ADR-011-cross-platform-product-ui.md) | Cross-platform product UI architecture (Phase 4.0) |
| [ADR-012-apple-catalog-acquisition-production-policy.md](ADR-012-apple-catalog-acquisition-production-policy.md) | Apple catalog acquisition production policy (Phase 5.3.3) |
| [ADR-013-multi-provider-platform-vision.md](ADR-013-multi-provider-platform-vision.md) | Multi-provider platform vision (Phase 5.4) |
| [ADR-016-playlist-sync-model.md](ADR-016-playlist-sync-model.md) | Sync model + conflict resolution (Phases 6.4–6.7) |
| [phase-4-ui-architecture.md](phase-4-ui-architecture.md) | Phase 4 UI implementation notes |

## Product (Phase 4)

See [../product/README.md](../product/README.md).

## Migration status

| PR / Phase | Scope | Status |
|------------|-------|--------|
| PR 1–9 | Canonical foundation, scoring, Apple gateways, acquisition | Done |
| PR 4.x | macOS shell, bridge, themes, history | Done |
| PR 5.x | Smart input, ProviderImportPort, acquisition SSOT | Done |
| Phase 6.1–6.7 | Provider platform, local SSOT, sync plan/apply, conflicts | Done (`main`) |
| Phase 6.8 | Product experience (SwiftUI) | In progress |
| OSS readiness | Contributor docs, governance, issue templates | In progress |

## Rules

1. Application code must depend on `canonical/` contracts, not provider SDKs.
2. Provider-specific code lives under `integration/` (future PRs).
3. Every architectural change requires an ADR when it affects boundaries or contracts.
