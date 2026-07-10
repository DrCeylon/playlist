# Architecture

Engineering overview for contributors. Decision records: [`architecture/`](architecture/).

## System context

```text
┌──────────────┐     JSON-RPC      ┌─────────────────────┐
│ ResonanceMac │ ◄──────────────► │ Python bridge_runtime│
│  (SwiftUI)   │   stdin/stdout   │  + use cases         │
└──────────────┘                   └──────────┬──────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
            │ playlist_    │         │ playlist_    │         │ integration/ │
            │ library/     │         │ sync/        │         │ <provider>/  │
            │ (local SSOT) │         │ (plan/apply) │         │ gateways     │
            └──────────────┘         └──────────────┘         └──────────────┘
```

## Layers

| Layer | Path | Rules |
|-------|------|-------|
| **Canonical** | `playlist_builder/canonical/` | Value types, enums — no I/O |
| **Application** | `playlist_builder/app/` | Use cases, orchestration |
| **Integration** | `playlist_builder/integration/` | Provider SDKs, AppleScript |
| **Bridge** | `ui/bridge/`, `app/bridge_runtime/` | JSON-RPC; thin handlers |
| **UI (Swift)** | `apps/resonance/` | Presentation; delegate to bridge |

**Dependency rule:** dependencies point inward. Providers never import application code.

## Key flows

### Generation

```text
PlaylistGenerationRequest → scoring engine → PlaylistDefinition → preview → import
```

### Import (Apple Music)

```text
PlaylistDefinition → ProviderImportPort → library resolve → acquire → deliver to Music.app
```

### Sync

```text
local playlist + remote snapshot → plan_sync → conflicts[] → resolve_sync_conflicts → apply_sync
```

Never mutate the local playlist directly during sync — always produce a new **plan**.

## Bounded contexts

| Context | Owns |
|---------|------|
| Composition | Seeds, scoring, sections |
| Acquisition | Track resolution, manual acquisition |
| Local library | `ManagedPlaylistDetail`, versioning |
| Sync | Plans, conflicts, operations audit |
| Providers | Gateways, auth, read/write ports |

## Swift packages

| Package | Role |
|---------|------|
| `ResonanceCore` | DTOs, bridge client, validation |
| `ResonanceDesign` | Theme tokens |
| `ResonanceMac` | App shell, views, view models |

## Bridge contract

28 commands — parity tested between Python `BridgeCommand` and Swift `BridgeCommand.allCases`.

See [phase-4-engine-bridge.md](product/phase-4-engine-bridge.md).

## ADR index

| ADR | Topic |
|-----|-------|
| [001](architecture/ADR-001-canonical-model.md) | Canonical model |
| [013](architecture/ADR-013-multi-provider-platform-vision.md) | Multi-provider vision |
| [014](architecture/ADR-014-provider-gateway-architecture.md) | Gateway architecture |
| [015](architecture/ADR-015-provider-auth-boundary.md) | Auth boundary |
| [016](architecture/ADR-016-playlist-sync-model.md) | Sync model |
| [017](architecture/ADR-017-remote-playlist-snapshot.md) | Remote snapshots |
| [018](architecture/ADR-018-experimental-youtube-music-gateway.md) | YouTube experimental |

Full list: [architecture/README.md](architecture/README.md)

## Quality & debt

- [QUALITY_AUDIT.md](QUALITY_AUDIT.md) — Staff Engineer review
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) — tracked items
- [OSS_READINESS_AUDIT.md](OSS_READINESS_AUDIT.md) — open source onboarding

## Testing strategy

| Layer | Tool |
|-------|------|
| Python unit/integration | `pytest` (~490 tests) |
| Architecture guards | `tests/test_sync_architecture.py`, provider-neutral guards |
| Swift | `swift test` (macOS CI) |
| Bridge parity | `tests/test_bridge_command_contract.py` |

Linux CI runs Python. macOS CI runs Swift + full bridge.
