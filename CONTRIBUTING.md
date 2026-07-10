# Contributing to Resonance

Thank you for your interest in Resonance. This guide helps you go from clone to merged PR.

## What you're contributing to

**Resonance** is a local-first playlist platform: Python engine + macOS SwiftUI app. See [docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md) for context and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design.

## Prerequisites

| Tool | Version | Required for |
|------|---------|--------------|
| Python | 3.12+ | All contributions |
| git | any recent | All |
| Xcode / Swift | latest stable | macOS app, Apple import |
| macOS | 13+ | Apple Music import, Swift CI parity |

## Setup (5 minutes)

```bash
git clone https://github.com/DrCeylon/playlist.git
cd playlist
./scripts/setup_dev.sh
source .venv/bin/activate
python -m pytest -q
```

Optional YouTube Music experimental gateway:

```bash
pip install -e ".[dev,youtube]"
```

## What runs where

| Capability | Linux CI | macOS |
|------------|----------|-------|
| Python unit tests (`pytest`) | ✅ | ✅ |
| Playlist generation (catalog) | ✅ | ✅ |
| Bridge JSON-RPC contract tests | ✅ | ✅ |
| Sync planning / conflict resolution | ✅ (mocks) | ✅ |
| Apple Music import / AppleScript | ❌ | ✅ |
| Resonance macOS app build | ❌ | ✅ |

Full local gate on macOS:

```bash
make check-all
```

## Repository tour

```
apps/resonance/          macOS app (Swift)
playlist_builder/
  canonical/             Provider-neutral types
  app/                   Use cases, sync, repository
  integration/           Provider gateways
  ui/bridge/             JSON-RPC protocol
tests/                   Python tests
docs/                    ADRs + contributor docs
wiki/                    French user documentation
```

## Architecture boundaries (required reading)

1. **Domain / use cases** must not import provider-specific SDKs.
2. **Provider code** lives only under `playlist_builder/integration/<provider>/`.
3. **Bridge DTOs** in `ui/shared/dto/` mirror Swift `ResonanceCore` — coordinate changes.
4. **Local repository** is the single source of truth for managed playlists.
5. **Sync** — never mutate playlists directly; always output a new plan.

See [docs/PROVIDER_PLATFORM.md](docs/PROVIDER_PLATFORM.md).

## Making changes

### Branch naming

```bash
git checkout -b cursor/my-feature-ef21   # or your-username/my-feature
```

### Before opening a PR

```bash
python -m pytest -q                     # required on all PRs
cd apps/resonance && ./scripts/build.sh # required if Swift or bridge changed
```

### PR guidelines

1. Rebase on `main`
2. One logical change per commit; clear messages
3. Reference issue or capability in title (prefer "Add sync conflict picker" over "Phase 6.8")
4. No functional behavior change unless the PR explicitly intends it
5. Update docs if you change bridge contracts, setup, or user-visible flows

### Code review focus

- Provider-neutral core respected?
- Tests added for new behavior?
- Bridge Swift/Python parity if DTOs changed?
- No secrets in logs or bridge payloads?

## Testing

```bash
python -m pytest -q                    # full suite
python -m pytest tests/test_sync_architecture.py -q   # arch guards
python -m pytest tests/test_bridge_command_contract.py -q
```

Swift (macOS):

```bash
cd apps/resonance && swift test
```

## Documentation

| Change type | Update |
|-------------|--------|
| New provider | ADR + `docs/PROVIDER_PLATFORM.md` matrix |
| Bridge command | Python `commands.py` + Swift `BridgeCommand` + contract test |
| User-facing feature (FR) | `wiki/` page |
| Architecture boundary | ADR in `docs/architecture/` |

Index: [docs/README.md](docs/README.md)

## AI agents

See [AGENTS.md](AGENTS.md) for automation-specific instructions.

## Community

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security](SECURITY.md)
- [Support](SUPPORT.md)
- [Governance](docs/GOVERNANCE.md)

## Getting stuck

Open a [GitHub Issue](https://github.com/DrCeylon/playlist/issues) with your environment, what you tried, and test output. See [SUPPORT.md](SUPPORT.md).
