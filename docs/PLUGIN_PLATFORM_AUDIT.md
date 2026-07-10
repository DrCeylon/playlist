# Plugin Platform Audit

**Audience:** maintainers preparing Resonance for VSCode / Home Assistant / JetBrains-style extensions  
**Date:** July 2026  
**Principle:** plugins never touch core directly — only stable contracts and extension points.

---

## Executive summary

| Question | Answer |
|----------|--------|
| Ready for **external** plugins today? | **No** — no loader, sandbox, or dynamic discovery |
| Ready for **in-repo** extensions today? | **Partial** — music providers + themes + discovery candidates |
| Strongest existing pattern? | `ProviderGatewayRegistry` + port protocols |
| Weakest link for plugins? | Hardcoded `factory.py`, closed Swift enums, monolithic bridge backend |
| What we ship in this PR? | Versioned extension API, extension point IDs, manifest validation, diagnostics |

**Verdict:** Resonance has the **right architectural instincts** (ports, registry, frozen bridge DTOs) but is a **modular monolith**, not a plugin host. Foundations laid here are immediately useful for versioning and documentation without speculative loaders.

---

## 1. Inspiration: VSCode, Home Assistant, JetBrains

| Platform | Pattern | Resonance equivalent today |
|----------|---------|---------------------------|
| **VSCode** | Extension manifest + activation events + contribution points | `ExtensionPointId` + `ExtensionManifest` (schema only) |
| **VSCode** | Stable `vscode.*` API; extensions in separate process | Bridge DTOs + port protocols (no separate process) |
| **Home Assistant** | `manifest.json` per integration + config flow | Provider gateway + `ProviderAuthPort` |
| **Home Assistant** | Core never imports integrations directly | `IntegrationGateway` routes via registry ✅ |
| **JetBrains** | Plugin descriptor + extension points XML | `ExtensionPointId` enum (code) |
| **JetBrains** | PSI/API sandbox via classloader boundaries | **Missing** — same Python process today |

**Target model for Resonance (2030):**

```text
┌─────────────────────────────────────────────────────────┐
│ Resonance Host (core — never imported by plugins)        │
│  canonical/ · playlist_sync/ · playlist_library/         │
│  ExtensionHost — dispatches by ExtensionPointId            │
└───────────────────────────┬─────────────────────────────┘
                            │ stable ports only
┌───────────────────────────▼─────────────────────────────┐
│ Extension packages (separate install / monorepo module)    │
│  manifest.json · permissions · api_version               │
│  registers: ProviderGateway | Theme | ExportFormat | …   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Extension points inventory

### Active today (in-process registration)

| Extension point | ID | Registry / hook | Contract | Plugin-ready |
|-----------------|-----|-----------------|----------|--------------|
| Music provider | `music_provider` | `ProviderGatewayRegistry` | `ProviderGateway` + ports | **Partial** — register in factory |
| UI theme | `theme` | `ThemeRegistry` | `Theme` JSON + validation | **Partial** — bundled JSON |
| Discovery candidate | `discovery_candidate` | `DiscoveryPipeline(providers=…)` | `CandidateProvider` ABC | **Partial** — list injection |
| Manual acquisition | (callback) | `ProviderImportPort.configure_manual_acquisition` | `ManualAcquisitionHook` | **Yes** — internal |
| Playlist repository | (DI) | `RepositoryProvider` | `ManagedPlaylistRepository` Protocol | **Yes** — inject impl |
| Sync components | (DI) | `ApplySyncPlaylist(...)` ctor | concrete classes | **Partial** — no registry |
| Bridge backend | (DI) | `JsonRpcEngineBridge(backend=…)` | duck-typed methods | **Partial** — subclass |

### Reserved (documented, no loader — YAGNI)

| Extension point | ID | Future contract sketch |
|-----------------|-----|------------------------|
| Sync strategy | `sync_strategy` | `PlaylistSyncPlanner` protocol swap |
| Conflict resolver | `conflict_resolver` | `PlaylistConflictResolver` strategy chain |
| Automation rule | `automation_rule` | Rule DSL evaluator (2.0) |
| AI engine | `ai_engine` | Opt-in suggestion port |
| Export format | `export_format` | `canonical playlist → bytes` |
| Import format | `import_format` | `file → RemotePlaylistSnapshot` |
| Dashboard widget | `dashboard_widget` | Swift `DashboardWidget` protocol (2030) |
| Analysis tool | `analysis_tool` | Read-only library analytics port |

---

## 3. Layer-by-layer analysis

### 3.1 ProviderGatewayRegistry

**Location:** `integration/gateway/registry.py`

| Aspect | Assessment |
|--------|------------|
| Pattern | Keyed registry, explicit `register()` |
| Discovery | **None** — only `factory.py` calls `register` |
| Extension point ID | `ExtensionPointId.MUSIC_PROVIDER` (this PR) |
| Protocol gaps | `auth`, `import_service` not on `ProviderGateway` — `getattr` escape hatches |

**Plugin implication:** first-party and monorepo plugins add `integration/<name>/` + one line in factory. External plugins need a **loader** (deferred).

### 3.2 Bridge (`ui/bridge/`)

| Aspect | Assessment |
|--------|------------|
| Commands | `BridgeCommand` StrEnum — **28 frozen commands** |
| Versioning | `BRIDGE_API_VERSION` in diagnostics (this PR) |
| Dispatch | `json_rpc.py` if/elif per command |
| Backend protocol | `EngineBridgeBackend` **incomplete** vs `RuntimeEngineBridgeBackend` |
| Extension | New command = enum + handler + Swift case + tests |

**Plugin implication:** bridge is the **public API** for UI extensions. Plugins should **not** add commands without ADR — host exposes stable commands; plugins register **handlers** behind extension points (future).

### 3.3 Use cases (`app/use_cases/`)

Thin layer; mostly wired in bridge runtime. **No registry.** `AutocompleteSearchUseCase` hardcodes Apple for artist/track.

**Plugin implication:** use cases become thin facades over extension host in 2.0 — not plugin-ready today.

### 3.4 Repositories (`app/playlist_library/`)

| Protocol | Swappable |
|----------|-----------|
| `ManagedPlaylistRepository` | ✅ via injection |
| `PlaylistSyncOperationRepository` | ✅ |
| Default | `JsonManagedPlaylistRepository` — paths from `AppSettings` |

**Plugin implication:** storage plugins (SQLite, Postgres) possible via repository injection — **no loader**.

### 3.5 Sync engine (`app/playlist_sync/`)

| Component | Injectable | Registry |
|-----------|------------|----------|
| `PlaylistSyncEngine` | ✅ ctor | ❌ |
| `PlaylistConflictResolver` | ✅ | ❌ |
| `SyncActionExecutor` | ✅ | ❌ — concrete class |
| `SyncMode` / enums | ❌ frozen | — |

**Plugin implication:** swap strategies by DI in factory today; **sync_strategy** extension point needs registry in 2.0.

### 3.6 Swift — ResonanceCore / ResonanceMac

| Surface | Extensible |
|---------|------------|
| `*Serving` protocols | ✅ test doubles |
| `BridgeTransport` | ✅ |
| `ProviderID`, `BridgeCommand` | ❌ closed enums |
| `AppShellView` navigation | ❌ hardcoded `switch` |
| `PythonEngineBridgeService` | ❌ monolith in Mac target |
| `ThemeRegistry` | ✅ JSON bundles |

**Plugin implication:** Swift UI plugins require route registry (2030). Engine plugins stay Python-side for foreseeable future.

### 3.7 DTOs (`ui/shared/dto/`, `ResonanceCore`)

Mirror Python ↔ Swift with contract tests. **Additive fields** OK with schema version bumps. **Closed enums** block silent extension.

---

## 4. Security, permissions, sandboxing

| Concern | Today | Target |
|---------|-------|--------|
| Secret leakage via bridge | `assert_bridge_safe_mapping` exists (YT); not global | Enforce on all provider auth responses |
| Plugin permissions | Schema defines `permissions[]` | Host checks before granting network/fs |
| Sandboxing | **None** — same process | Subprocess or restricted importlib (2030) |
| API compatibility | `EXTENSION_API_VERSION` + major match | Semver policy in ADR-020 |
| Supply chain | Monorepo only | Signed manifests (2030) |

### Permission model (schema — not enforced yet)

| Permission | Grants |
|------------|--------|
| `network` | HTTP client in integration layer |
| `filesystem.read` | Read user-selected paths |
| `filesystem.write` | Write reports, caches |
| `provider.auth` | `ProviderAuthPort` connect |
| `provider.library` | Library resolve / delivery |
| `bridge.events` | Emit diagnostic events |
| `library.read` | Read managed playlists |
| `library.write` | Mutate SSOT |

---

## 5. Version compatibility

| API | Version constant | Location |
|-----|------------------|----------|
| Extension manifest | `EXTENSION_API_VERSION` | `platform/api_version.py` |
| Bridge commands | `BRIDGE_API_VERSION` | `platform/api_version.py` |
| Engine | `__version__` | diagnostics `engine_version` |

**Rule:** manifest `api_version` major must match host. Minor/patch additive.

---

## 6. What blocks external plugins (honest list)

1. No `importlib` / entry-point loader
2. No subprocess isolation
3. Factory hardcodes registration
4. Swift closed enums (`ProviderID`, `BridgeCommand`, `SidebarItem`)
5. Incomplete `EngineBridgeBackend` protocol
6. No permission enforcement layer
7. No extension marketplace / signing
8. Bilateral Python+Swift contract for every bridge change

---

## 7. Foundations implemented (this PR)

| Deliverable | Immediate utility |
|-------------|-------------------|
| `platform/extension_points.py` | Stable IDs for docs + diagnostics |
| `platform/api_version.py` | Compatibility checking |
| `platform/manifest.py` | Validate manifests without loading code |
| `schemas/resonance-extension-manifest.schema.json` | Contributor contract |
| Diagnostics `extension_api_version` | Clients can detect host capability |
| `ProviderGatewayRegistry.extension_point_id` | Documents first extension point |
| Architecture tests | `platform/` isolation from `integration/` |

**Explicitly NOT implemented:** loader, sandbox, plugin marketplace, Swift route registry, empty `extensions/` package.

---

## 8. Path to real plugins

| Phase | Work |
|-------|------|
| **Now** | Monorepo modules + manifest validation + port protocols |
| **1.0** | Entry-point discovery for `music_provider` only (`pyproject.toml` optional group) |
| **2.0** | `export_format`, `automation_rule` registries |
| **2030** | Subprocess plugins, Swift dashboard widgets, public API |

---

## References

- [ADR-020](architecture/ADR-020-plugin-platform-foundations.md)
- [guides/plugin-development.md](guides/plugin-development.md)
- [ADR-013](architecture/ADR-013-multi-provider-platform-vision.md)
- [ADR-014](architecture/ADR-014-provider-gateway-architecture.md)
- [TARGET_ARCHITECTURE.md](architecture/TARGET_ARCHITECTURE.md) (if merged from vision PR)
