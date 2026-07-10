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
| **Users** | Issues, wiki feedback, no merge rights |

There is no formal foundation or paid governance body. Decisions are made by maintainers with transparency via ADRs and GitHub discussions.

## Decision process

| Change type | Process |
|-------------|---------|
| Bug fix, tests, docs | PR + review → merge to `main` |
| New provider gateway | ADR + architecture review + tests |
| Breaking bridge contract | ADR + Swift/Python parity tests + migration note |
| Product direction | Update [ROADMAP.md](ROADMAP.md) + ADR if architectural |

**Architecture Decision Records** live in `docs/architecture/ADR-*.md`. Significant boundary changes require a new or updated ADR before merge.

## Branch policy

- **`main`** — always deployable; protected by CI
- **Feature branches** — `cursor/<topic>-ef21` or contributor-chosen names
- **Stale branches** — may be deleted after merge; see [wiki/Maintenance-et-Workflow.md](../wiki/Maintenance-et-Workflow.md)

## Releases

Releases are tagged on `main` when maintainers judge a milestone stable. Until regular releases exist:

- Consumers track `main` commit SHA
- Test count and phase status: [wiki/Etat-des-Phases.md](../wiki/Etat-des-Phases.md)

## Licensing

[MIT](../LICENSE) — contributions are accepted under the same license unless otherwise noted.

## Code of Conduct

Enforcement per [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md).

## Relationship to employer / commercial use

Resonance is a personal open-source project. It is not affiliated with any employer. Commercial use of the MIT-licensed code is permitted with attribution.

## Future governance

If contributor volume grows (>10 active contributors), consider:

- `MAINTAINERS.md` with named owners per area
- GitHub teams for review assignment
- RFC process for large changes

Not required at current scale.
