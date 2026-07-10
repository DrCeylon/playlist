# PR Review Checklist

Use before approving a Resonance PR. Any unchecked item must be justified in the review.

## Scope

- [ ] **Scope respected** — PR does what was requested, nothing more (no unrequested UX or new epic)

## Architecture

- [ ] **No provider-specific in core** — no `integration.<provider>` imports outside `integration/`; no provider IDs in canonical contracts
- [ ] **Bridge runtime stays neutral** — no AppleScript or direct Apple imports in `bridge_runtime/`
- [ ] **Dependencies inward** — canonical → app → ports → integration
- [ ] **ADR updated** if boundaries or contracts changed

## Tests

- [ ] **`python3.12 -m pytest -q` green** — tests added/updated for new behavior
- [ ] **Swift tests/build** on macOS if Swift or bridge DTOs changed (or absence justified on Linux)

## Documentation

- [ ] **Docs updated** if contracts, limits, or onboarding changed
- [ ] **No stale phase/PR references** introduced

## Quality

- [ ] **Technical debt** stable or reduced; new debt documented in `TECHNICAL_DEBT.md`
- [ ] **UX unchanged** unless explicitly requested
- [ ] **Migration** noted if data/schema migration required, or confirmed not needed

## Delivery

- [ ] **Clear summary** — files touched, validation (real test results), git state, next step
