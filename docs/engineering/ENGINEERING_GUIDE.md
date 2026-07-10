# Engineering Guide

Durable engineering rules for Resonance contributors and agents. Complements [AGENTS.md](../../AGENTS.md). Priority: explicit user instruction > AGENTS.md > accepted ADRs > this guide.

## Product principle

Resonance is a **universal playlist platform**. Apple Music is a **provider**, not the product center. The local repository is SSOT; providers resolve, acquire, and deliver.

## Definition of Done

A task is done only when:

1. Requested scope is complete — no scope creep
2. Architecture invariants respected ([AGENTS.md](../../AGENTS.md))
3. `python3.12 -m pytest -q` passes (Swift build/test on macOS when Swift changed)
4. New behavior has appropriate tests
5. Docs/ADR updated if contracts or boundaries changed
6. UX unchanged unless explicitly requested
7. Structured final report: files, summary, validation, git state, next step
8. Changes committed and pushed; PR created or updated

## Stop criteria (agents)

Stop when:

- Definition of Done is met for the scoped task, **or**
- **Blocked** — missing dependency, product decision, ADR, or secret — report clearly; do not expand scope, **or**
- Continuing requires **out-of-scope work** (new epic, UX redesign, new provider without ADR)

## ADR workflow

| Step | Action |
|------|--------|
| 1 | Create `docs/architecture/ADR-<NNN>-<slug>.md` with Status: Proposed |
| 2 | Include Context, Decision, Consequences, References |
| 3 | New **provider** requires dedicated ADR before implementation |
| 4 | Maintainer accepts → Status: Accepted; update [architecture/README.md](../architecture/README.md) |
| 5 | Superseded ADRs → Status: Superseded with link to replacement |

Full ADR catalog: [docs/architecture/README.md](../architecture/README.md). Do not duplicate ADR content in other hubs.

## Escalation

| Situation | Action |
|-----------|--------|
| Product / priority ambiguity | Stop; document question; do not guess |
| New provider or breaking bridge contract | Propose ADR; stop code until Accepted |
| Security concern | Follow [SECURITY.md](../../SECURITY.md); do not discuss publicly |
| UX change not in task | Revert or stop; request explicit approval |
| CI red on main | Fix or document blocker; do not merge failing work |

## Review

All PRs: [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md)

## Current state pointers (living docs)

| Topic | Canonical doc |
|-------|----------------|
| Roadmap | [ROADMAP.md](../ROADMAP.md) |
| Backlog | [product/BACKLOG.md](../product/BACKLOG.md) |
| Technical debt | [TECHNICAL_DEBT.md](../TECHNICAL_DEBT.md) |
| Known limits | [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md) |
| Phase tracker (French) | [wiki/Etat-des-Phases.md](../../wiki/Etat-des-Phases.md) |

Do **not** use frozen "current phase" files — they go stale. Use the table above.
