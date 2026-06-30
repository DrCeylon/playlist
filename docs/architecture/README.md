# Architecture

This directory contains the long-lived architectural documentation for Playlist Builder.

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

## Migration status

| PR | Scope | Status |
|----|-------|--------|
| PR 1 | `canonical/` foundation, Python 3.12, remove legacy `generation/` | Done |
| PR 2 | Unified scoring engine | Done |
| PR 3 | Identity cache infrastructure | Done |
| PR 4 | Apple catalog provider gateway | Done |
| PR 5 | Apple delivery + resolution pipeline | Done |
| PR 6 | Observable Apple Music resolution pipeline | Done |
| PR 7 | Catalog fallback advisory on library miss | Done |
| PR 8 | Application platform + catalog-to-library acquisition | Done |
| PR 9 | Generate playlist via AppContext + gateway unification | Planned |
| PR 10 | Generic resolution trace + legacy shim removal | Planned |

## Rules

1. Application code must depend on `canonical/` contracts, not provider SDKs.
2. Provider-specific code lives under `integration/` (future PRs).
3. Every architectural change requires an ADR when it affects boundaries or contracts.
