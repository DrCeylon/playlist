# AGENTS.md — Resonance

Instructions for AI coding agents working on this repository.

## What this project is

**Resonance** — local-first, multi-provider playlist platform. Python engine + macOS SwiftUI app. The local playlist repository is the single source of truth.

## Repository map

| Path | Role |
|------|------|
| `playlist_builder/canonical/` | Provider-neutral types — never import from `integration/` |
| `playlist_builder/app/` | Use cases, sync engine, repository, bridge runtime |
| `playlist_builder/integration/<provider>/` | Provider-specific I/O only |
| `playlist_builder/ui/bridge/` | JSON-RPC commands & DTOs |
| `apps/resonance/ResonanceCore/` | Swift DTO mirrors + bridge client |
| `apps/resonance/ResonanceMac/` | SwiftUI app — no provider SDKs in views |
| `tests/` | Python tests — run before every PR |

## Hard invariants (never break)

- `ProviderImportPort` — frozen contract
- `plan_sync` — pure, no side effects
- `apply_sync` — separate from planning, validated
- `ManagedPlaylistRepository` — local SSOT
- `RemotePlaylistSnapshot` — immutable
- `ProviderGatewayRegistry` — provider registration
- Sync conflict engine — provider-neutral

## Development commands

```bash
pip install -e ".[dev]"
python -m pytest -q

# Full gate (macOS only)
./scripts/check_all.sh

# Swift only
cd apps/resonance && ./scripts/build.sh
```

## Branch & PR conventions

- Branch: `cursor/<descriptive-name>-ef21`
- Base: `main`
- Run `pytest -q` before push
- See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)

## Release context

Target public version: **v1.0.0**. Version source: `playlist_builder.__version__`.  
Known limits: [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md).
