# Contributing to Resonance

Thank you for your interest in Resonance. This guide helps you go from clone to merged PR.

## What you're contributing to

**Resonance** is a local-first playlist platform: Python engine + macOS SwiftUI app.

- Product context: [wiki/Vision-et-Objectif.md](wiki/Vision-et-Objectif.md)
- Architecture: [docs/architecture/vision.md](docs/architecture/vision.md)
- Provider platform: [docs/product/phase-6-provider-platform.md](docs/product/phase-6-provider-platform.md)
- Release status: [docs/RELEASE_PLAN.md](docs/RELEASE_PLAN.md)
- Quality baseline: [docs/QUALITY_AUDIT.md](docs/QUALITY_AUDIT.md)

## Prerequisites

| Tool | Version | Required for |
|------|---------|--------------|
| Python | 3.12+ | All contributions |
| git | any recent | All |
| Xcode / Swift | latest stable | macOS app, Apple import |
| macOS | 14+ recommended | Apple Music import, Swift CI parity |

## Setup

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
| Python unit tests (`pytest`) | Yes | Yes |
| Playlist generation (catalog) | Yes | Yes |
| Bridge JSON-RPC contract tests | Yes | Yes |
| Sync planning / apply (mocks) | Yes | Yes |
| Apple Music import / AppleScript | No | Yes |
| Resonance macOS app build | No | Yes |

Full local gate on macOS:

```bash
./scripts/check_all.sh
# or: make check-all
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
docs/                    ADRs + release docs
wiki/                    French user documentation
```

## Architecture boundaries

1. Domain / use cases must not import provider-specific SDKs.
2. Provider code lives only under `playlist_builder/integration/<provider>/`.
3. Bridge DTOs in `ui/shared/dto/` mirror Swift `ResonanceCore` — coordinate changes.
4. Local repository is the single source of truth for managed playlists.
5. Sync — `plan_sync` is pure; `apply_sync` is separate and validated.

## Making changes

### Branch naming

```bash
git checkout -b cursor/my-feature-ef21
```

### Commits

- One logical change per commit
- Clear messages in English or French
- Run `python -m pytest -q` before push

### Pull requests

Use the PR template. Ensure:

- Tests pass (CI Python on Linux; Swift on macOS when touching `apps/resonance/`)
- No unintended functional regressions
- ADR updated if architecture contracts change
- Release docs updated if user-visible limitations shift

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Questions

Open a [discussion or issue](https://github.com/DrCeylon/playlist/issues) — label `question` for general help.
