# ADR-001: Canonical domain model

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** Lead Architecture

## Context

The codebase started as an Apple Music utility. Sprint 2 introduced discovery and
planning, but domain types still leak provider concepts (`CatalogMatch`, Apple JSON
fields in discovery, AppleScript in the music client).

The product target is a multi-provider platform (Apple Music, Spotify, YouTube
Music, Deezer, Discogs, MusicBrainz, and more). At projected scale (500k+ LOC,
20 developers), ad hoc provider fields in shared models will become unmaintainable.

## Decision

Introduce a `playlist_builder.canonical` package as the innermost architectural
layer.

### Canonical package contents

| Module | Responsibility |
|--------|----------------|
| `models.py` | Provider-neutral value objects |
| `enums.py` | `ProviderId`, `ImportStatus`, `ResolutionDecision`, … |
| `identity.py` | Stable `track_identity_key()` for cache and dedup |
| `validation.py` | Canonical invariants |
| `contracts.py` | `Protocol` ports for provider gateways |
| `compat.py` | Temporary mapping to legacy `TrackRef` types |
| `constants.py` | Shared defaults such as playlist description |

### Legacy compatibility (PR 1)

- Keep `core.TrackRef` and JSON loaders unchanged for existing CLIs.
- Add `TrackRef.to_canonical()` / `TrackRef.from_canonical()` shims.
- Align `TrackRef.key` with `track_identity_key()` for consistent cache keys.
- Remove the unused `generation/` package.

### Python version

Raise `requires-python` to `>=3.12` to standardize on `StrEnum`, `slots=True`,
and modern typing for all new code.

## Consequences

### Positive

- Clear boundary for future provider gateways
- Testable contracts without Apple Music mocks
- Stable identity keys for cross-provider caching
- Removes duplicate legacy generation models

### Negative / trade-offs

- Temporary duplication between legacy and canonical models during migration
- Slight import indirection via `compat.py` until PR 8 cleanup

## Follow-up PRs

1. PR 2 — unified scoring engine
2. PR 3 — identity cache
3. PR 4+ — provider gateways and generic orchestrator

## Rejected alternatives

### Enrich `core/models.py` in place

Rejected because provider-specific types would continue to accumulate in the shared
core and violate Open/Closed at scale.

### Big-bang rewrite

Rejected because the current JSON-based compose → deliver workflow is stable and
must keep working for users during migration.
