# AGENTS.md — Resonance

Instructions for AI coding agents (Cursor Cloud, Copilot, etc.) working on this repository.

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
- Sync conflict engine — provider-neutral (no Apple/Spotify/YouTube in detector)

## Development commands

```bash
# Minimum gate (Linux or macOS)
pip install -e ".[dev]"
python -m pytest -q

# Full gate (macOS only)
make check-all

# Swift only
cd apps/resonance && ./scripts/build.sh
```

## Branch & PR conventions

- Branch: `cursor/<descriptive-name>-ef21`
- Base: `main`
- One logical change per commit
- Run `pytest -q` before push
- Touch Swift/bridge → run macOS build if available
- Draft PRs welcome

## What works without macOS

- All Python unit tests (mocks for Apple/YouTube)
- Generation, scoring, sync planning, conflict resolution
- Bridge contract tests

## What requires macOS

- Apple Music import (AppleScript)
- Swift app build & tests
- End-to-end provider import

## Documentation hierarchy

1. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design
2. [docs/PROVIDER_PLATFORM.md](docs/PROVIDER_PLATFORM.md) — provider boundaries
3. [docs/architecture/ADR-*.md](docs/architecture/) — decision records
4. [CONTRIBUTING.md](CONTRIBUTING.md) — human contributor guide
5. [wiki/](wiki/) — French end-user docs

## Common pitfalls

- Do not add provider-specific code outside `integration/<provider>/`
- Do not mutate playlists directly during sync — always produce a new plan
- Do not put business logic in Swift ViewModels — delegate to bridge services
- `ui/shared/dto/` is shared with Swift; changing fields requires both sides + tests
- README/wiki may lag; trust `pytest` and ADRs over stale phase docs

## Optional dependencies

```bash
pip install -e ".[dev,youtube]"   # YouTube Music experimental gateway
```

## Phase vocabulary

Internal history uses numbered phases (4.x, 5.x, 6.x). Prefer describing **capabilities** in PR titles (e.g. "sync conflict resolution") over phase numbers for external readability.
