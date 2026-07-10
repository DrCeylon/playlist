# Governance

## Project identity

| Name | Meaning |
|------|---------|
| **Resonance** | Product name — macOS app and long-term platform |
| **playlist-builder** | Python package name (`pip install -e .`) |
| **playlist** | GitHub repository name (historical) |

## Roles

| Role | Responsibility |
|------|----------------|
| **Maintainer(s)** | Merge PRs, release tags, security response, roadmap |
| **Contributors** | PRs via [CONTRIBUTING.md](../CONTRIBUTING.md) |
| **Users** | Issues, wiki feedback |

There is no formal foundation. Decisions are made by maintainers with transparency via ADRs and GitHub issues.

## Decision process

| Change type | Process |
|-------------|---------|
| Bug fix, tests, docs | PR + review → merge to `main` |
| New provider gateway | ADR + architecture review + tests |
| Breaking bridge contract | ADR + Swift/Python parity tests + migration note |
| Product direction | Update wiki + ADR if architectural |

**Architecture Decision Records** live in `docs/architecture/ADR-*.md`.

## Branch policy

- **`main`** — always deployable; protected by CI
- **Feature branches** — `cursor/<topic>-ef21` or contributor names
- **Stale branches** — deleted after merge when possible

## Releases

- Tagged on `main` when [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) is complete
- First public target: **v1.0.0**
- Status: [RELEASE_PLAN.md](RELEASE_PLAN.md), [wiki/Etat-des-Phases.md](../wiki/Etat-des-Phases.md)

## Licensing

[MIT](../LICENSE) — contributions accepted under the same license.

## Code of Conduct

[CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)

## Commercial use

Resonance is a personal open-source project. MIT license permits commercial use with attribution.
