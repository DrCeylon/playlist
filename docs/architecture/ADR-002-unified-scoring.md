# ADR-002: Unified scoring engine

- **Status:** Accepted
- **Date:** 2026-06-29
- **Depends on:** ADR-001

## Context

The codebase had three independent scoring implementations:

| Module | Purpose | Scale |
|--------|---------|-------|
| `catalog/scoring.py` | iTunes/MusicKit API result picking | 0–100 substring |
| `planning/scoring.py` | User constraint boosts/penalties | unbounded float |
| `resolver/scoring.py` | Fuzzy library match scoring | 0–100 fuzzy |

`resolver/scoring.py` was tested but not wired into the import pipeline. Thresholds
and normalization were duplicated across packages.

At multi-provider scale, each new integration must not reimplement matching logic.

## Decision

Create `playlist_builder.scoring` as the single scoring layer with three engines:

| Engine | Module | Responsibility |
|--------|--------|----------------|
| Match | `match_engine.py` | Catalog substring + fuzzy similarity scoring |
| Constraint | `constraint_engine.py` | Planning inclusion/exclusion adjustments |
| Resolution | `resolution.py` | Rank/select resolution candidates |

Shared infrastructure:

- `constants.py` — all thresholds and weights in one place
- `normalization.py` — shared text normalization and tokenization
- `models.py` — `MatchScore`, `ScoredMatch` value objects

Legacy modules (`catalog/scoring.py`, `planning/scoring.py`, `resolver/scoring.py`,
`resolver/normalization.py`) become thin facades re-exporting the unified engine.

## Resolution pipeline foundation

`scoring.resolution` introduces provider-neutral types:

- `ResolutionCandidate`
- `ResolutionDecision`
- `select_best_resolution()`

These prepare PR 5 (delivery gateway) without changing AppleScript behavior yet.

## Consequences

### Positive

- One place to tune thresholds for 10+ providers
- Fuzzy and catalog strategies share normalization
- Resolution ranking is testable without Apple Music
- Facades preserve backward compatibility during migration

### Trade-offs

- `constraint_engine` still depends on `planning.models.CandidateTrack` until PR 6
  moves application models behind canonical DTOs
- `canonical.identity` and `scoring.normalization` remain separate until PR 8

## Follow-up

- PR 5: wire `select_best_resolution()` into Apple delivery gateway
- PR 8: remove scoring facades and duplicate normalization
