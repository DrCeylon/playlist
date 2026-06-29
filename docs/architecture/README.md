# Architecture

This directory contains the long-lived architectural documentation for Playlist Builder.

## Documents

| Document | Purpose |
|----------|---------|
| [vision.md](vision.md) | Target platform architecture and bounded contexts |
| [ADR-001-canonical-model.md](ADR-001-canonical-model.md) | Canonical domain model decision record |
| [ADR-002-unified-scoring.md](ADR-002-unified-scoring.md) | Unified scoring engine decision record |

## Migration status

| PR | Scope | Status |
|----|-------|--------|
| PR 1 | `canonical/` foundation, Python 3.12, remove legacy `generation/` | In progress |
| PR 2 | Unified scoring engine | In progress |
| PR 3 | Identity cache infrastructure | Planned |
| PR 4 | Apple catalog provider gateway | Planned |
| PR 5 | Apple delivery + resolution pipeline | Planned |
| PR 6 | Application layer reorganization | Planned |
| PR 7 | Generic integration gateway registry | Planned |
| PR 8 | Final cleanup and shim removal | Planned |

## Rules

1. Application code must depend on `canonical/` contracts, not provider SDKs.
2. Provider-specific code lives under `integration/` (future PRs).
3. Every architectural change requires an ADR when it affects boundaries or contracts.
