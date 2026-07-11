# AGENTS.md — Resonance

Short, authoritative instructions for AI agents and cloud workers. Details: [docs/engineering/ENGINEERING_GUIDE.md](docs/engineering/ENGINEERING_GUIDE.md).

## Product identity

**Resonance** is a **local-first, multi-provider playlist platform** — not an Apple Music app. Apple Music is one provider among others. The **managed playlist repository** is the single source of truth.

## Repository map

| Path | Role |
|------|------|
| `playlist_builder/canonical/` | Provider-neutral types — never import from `integration/` |
| `playlist_builder/app/` | Use cases, sync engine, repository, bridge runtime |
| `playlist_builder/integration/<provider>/` | Provider-specific I/O only |
| `playlist_builder/ui/bridge/` | JSON-RPC commands & DTOs |
| `apps/resonance/ResonanceCore/` | Swift DTO mirrors + bridge client |
| `apps/resonance/ResonanceMac/` | SwiftUI app — no provider SDKs in views |
| `tests/` | Python tests — required before every PR |
| `docs/` | ADRs, release docs, engineering guides |
| `wiki/` | French user documentation |

## Hard invariants (never break)

- `ProviderImportPort` — frozen import contract
- `plan_sync` — pure, no side effects
- `apply_sync` — separate from planning, validated
- `ManagedPlaylistRepository` — local SSOT
- `RemotePlaylistSnapshot` — immutable
- `ProviderGatewayRegistry` — provider registration
- Sync conflict engine — provider-neutral
- No provider-specific imports in `canonical/` or sync planning core

## Commands (verified)

```bash
pip install -e ".[dev]"
python3.12 scripts/check_environment.py
python3.12 -m pytest -q                    # ~582 pass, 1 skip (~2 min)

# macOS full gate
./scripts/check_all.sh

# Swift only (macOS)
cd apps/resonance && ./scripts/build.sh
```

On **Linux / Cursor Cloud**: run `check_environment.py` + `pytest` only. Swift and `create_playlist.py` (AppleScript) require macOS. See [docs/engineering/CLOUD_AGENT_SETUP.md](docs/engineering/CLOUD_AGENT_SETUP.md).

## Branch & PR conventions

- Branch: `cursor/<descriptive-name>-ef21` (lowercase)
- Base: `main`
- Run `python3.12 -m pytest -q` before push
- Review: [docs/engineering/REVIEW_CHECKLIST.md](docs/engineering/REVIEW_CHECKLIST.md)
- Contributor flow: [CONTRIBUTING.md](CONTRIBUTING.md)

## Release context

- Version source: `playlist_builder.__version__` and `pyproject.toml` (currently **1.0.0** in tree — tagging requires maintainer approval)
- Limits: [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md)
- **Do not publish or tag a release** unless explicitly asked by the maintainer

## Documentation map

| Need | Document |
|------|----------|
| All docs index | [docs/README.md](docs/README.md) |
| Engineering DoD / ADR / stop rules | [docs/engineering/ENGINEERING_GUIDE.md](docs/engineering/ENGINEERING_GUIDE.md) |
| Cloud agent setup | [docs/engineering/CLOUD_AGENT_SETUP.md](docs/engineering/CLOUD_AGENT_SETUP.md) |
| Architecture ADRs | [docs/architecture/README.md](docs/architecture/README.md) |
| Governance | [docs/GOVERNANCE.md](docs/GOVERNANCE.md) |
