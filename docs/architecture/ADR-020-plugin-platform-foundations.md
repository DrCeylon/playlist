# ADR-020 — Plugin platform foundations

## Status

Accepted — July 2026. Documentation + minimal versioned contracts; no dynamic plugin loader.

## Context

Resonance must evolve toward VSCode / Home Assistant / JetBrains-style extensibility:

- New music providers, sync strategies, conflict resolvers, rules, AI engines, exports, imports, dashboards, analysis tools
- Plugins **never** import `playlist_sync/`, `playlist_library/`, or bridge internals directly
- Stable contracts and extension points only

Today the codebase is a **modular monolith** with one real registry (`ProviderGatewayRegistry`) and several injection-based extension patterns (themes, discovery, repositories).

See [PLUGIN_PLATFORM_AUDIT.md](../PLUGIN_PLATFORM_AUDIT.md).

## Decision

### Extension point model

1. Every extension category has a stable `ExtensionPointId` string (enum in `playlist_builder/platform/extension_points.py`).
2. Only **active** extension points have host registries today: `music_provider`, `theme`, `discovery_candidate`.
3. Reserved IDs document future tiers without implementing loaders (YAGNI).

### Versioned APIs

| API | Constant | Compatibility |
|-----|----------|---------------|
| Extension manifest | `EXTENSION_API_VERSION` | Major version must match |
| Bridge JSON-RPC | `BRIDGE_API_VERSION` | Documented alongside `BridgeCommand` enum |

Diagnostics expose both versions (additive JSON fields).

### Extension manifest

Plugins describe themselves with a JSON manifest validated by `parse_extension_manifest()` and `schemas/resonance-extension-manifest.schema.json`.

Required fields: `id`, `extension_point`, `api_version`, `entry`.

Manifest validation does **not** import or execute `entry`.

### Permissions (declarative only)

Manifest may declare `permissions[]`. Host enforcement deferred until a loader exists — schema documents intent.

### Sandboxing

**No sandbox in this ADR.** External plugins remain out of scope until subprocess or restricted loader ADR.

### What plugins may NOT do

- Import `playlist_builder.app.playlist_sync` from integration packages
- Import `integration.*` from sync engine
- Add bridge commands without ADR + Swift parity
- Bypass `ProviderGatewayRegistry` for music I/O
- Store provider OAuth secrets in bridge responses

### Registration today (in-process)

| Extension point | How to register |
|-----------------|-----------------|
| `music_provider` | Implement `ProviderGateway` → `registry.register()` in `factory.py` |
| `theme` | `ThemeRegistry.register(theme)` |
| `discovery_candidate` | Pass `CandidateProvider` into `DiscoveryPipeline` |

Future: optional `pyproject.toml` entry points for `music_provider` only (1.0 epic).

## Consequences

### Positive

- Clear vocabulary for contributors and future loader work
- Version surface for compatibility checks
- Diagnostics help clients detect capabilities

### Trade-offs

- Reserved extension point IDs may never ship — acceptable documentation cost
- Manifest permissions not enforced yet — documented honestly

## References

- [PLUGIN_PLATFORM_AUDIT.md](../PLUGIN_PLATFORM_AUDIT.md)
- [guides/plugin-development.md](../guides/plugin-development.md)
- [ADR-014](ADR-014-provider-gateway-architecture.md)
