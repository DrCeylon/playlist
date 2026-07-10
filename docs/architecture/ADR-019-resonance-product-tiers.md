# ADR-019 — Resonance product tiers and architectural boundaries

## Status

Accepted — July 2026. Documentation only; no runtime change.

## Context

Resonance has reached technical maturity (sync engine, SSOT, conflict resolution, multi-provider registry). The product team needs explicit **tier boundaries** (MVP, 1.0, 2.0, 2030) so engineering decisions do not over-build or under-build relative to vision.

See [RESONANCE_VISION_2030.md](../product/RESONANCE_VISION_2030.md).

## Decision

### Product tiers

| Tier | Year (target) | User promise | Technical scope |
|------|---------------|--------------|-----------------|
| **MVP** | 2026 | Compose + deliver (Apple); sync foundations | Current codebase |
| **1.0** | 2027 | Public OSS; 2 providers; trustworthy sync UX | + gateways, UX, OSS |
| **2.0** | 2028 | Personal library OS: rules, undo, multi-destination | + rules, schedule, undo modules |
| **2030** | 2030 | Open infrastructure; API; plugins; ecosystem | + plugin host, public API, optional cloud metadata |

### Differentiators by tier

| Differentiator | First appears |
|----------------|---------------|
| Generation + scoring | MVP |
| Local SSOT + snapshots | MVP |
| Sync with conflict resolution | MVP |
| Second production provider | 1.0 |
| Match confidence visible | 1.0 |
| Declarative rules | 2.0 |
| Undo / versioning UI | 2.0 |
| Multi-destination sync | 2.0 |
| Local HTTP API | 2.0 |
| Public API + plugins | 2030 |
| Collaborative metadata (cloud) | 2030 |

### Architectural boundaries (unchanged)

1. **Music Providers** live in `ProviderGatewayRegistry` — never Resonance Identity.
2. **Resonance Services** (future cloud) sync metadata only — never audio, never provider OAuth.
3. **Rules engine** (2.0) mutates local SSOT; sync is explicit downstream.
4. **Undo** operates on local mutations; provider revert is a separate user-triggered sync.
5. **Plugins** (2030) extend registry and rules — never patch core sync engine in place.

### What we will not build (any tier)

- Audio hosting or streaming
- DRM circumvention
- Centralized OAuth secret broker
- Provider-specific logic in `playlist_sync/`
- Mandatory cloud account
- Mandatory LLM / AI

### Immediate preparation (no speculative code)

Documented in [ARCHITECTURAL_PREP.md](../product/ARCHITECTURAL_PREP.md):

- Preserve `playlist_version`, immutable snapshots, sync operation log
- Extend entities with optional fields rather than new parallel stores
- Add ADRs before bridge contract changes
- Create new packages (`rules/`, `undo/`) only when epic starts

## Consequences

### Positive

- Clear answer to "should we build X now?" → check tier + YAGNI
- Contributors align on 2.0 without guessing
- Marketing / OSS story coherent

### Trade-offs

- Tier dates are targets, not commitments
- Some 2.0 features could ship early if justified (exception needs ADR note)

## References

- [ROADMAP.md](../ROADMAP.md)
- [BACKLOG.md](../product/BACKLOG.md)
- [TARGET_ARCHITECTURE.md](TARGET_ARCHITECTURE.md)
- [ADR-013](ADR-013-multi-provider-platform-vision.md)
