# Architecture

This directory contains the long-lived architectural documentation for **Resonance**.

## Start here

| Document | Purpose |
|----------|---------|
| [vision.md](vision.md) | Engineering vision and layering |
| [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md) | Target state for Resonance 2.0 |
| [../product/RESONANCE_VISION_2030.md](../product/RESONANCE_VISION_2030.md) | Product vision 2030 |
| [ADR-019-resonance-product-tiers.md](ADR-019-resonance-product-tiers.md) | MVP / 1.0 / 2.0 / 2030 boundaries |

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
| [ADR-019-resonance-product-tiers.md](ADR-019-resonance-product-tiers.md) | Product tiers and architectural boundaries |
| [ADR-020-plugin-platform-foundations.md](ADR-020-plugin-platform-foundations.md) | Plugin platform foundations |
| [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md) | Target architecture for Resonance 2.0 |
| [phase-4-ui-architecture.md](phase-4-ui-architecture.md) | Phase 4 UI implementation notes |

## Product (Phase 4)

See [../product/README.md](../product/README.md).

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
| PR 9 | Phases 2–3 gateway unification + E2E documentation | Done |
| PR 10 | Generic resolution trace + legacy shim removal | Planned |
| PR 4.0 | Product UI discovery & architecture (docs) | Done |
| PR 4.1 | Shared UI DTO + validation contracts | Done |
| PR 4.2 | Engine Bridge JSON protocol | In progress |
| PR 4.2–4.9 | UI implementation roadmap | Largely done (macOS shell, import UX, history) |
| PR 5.3 | Performance + acquisition policy (ADR-012) | Done |
| PR 5.4 | Architecture consolidation (ADR-013, no runtime change) | Done |
| PR 5.5+ | ProviderImportPort, bridge decoupling | Planned |

## Release engineering (v1.0)

| Document | Purpose |
|----------|---------|
| [RELEASE_PLAN.md](../RELEASE_PLAN.md) | Release milestones and go/no-go |
| [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) | Pre-tag checklist |
| [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) | User-facing limitations |
| [GOVERNANCE.md](../GOVERNANCE.md) | Project governance |

## Rules

1. Application code must depend on `canonical/` contracts, not provider SDKs.
2. Provider-specific code lives under `integration/` (future PRs).
3. Every architectural change requires an ADR when it affects boundaries or contracts.
