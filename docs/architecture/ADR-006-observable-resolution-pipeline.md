# ADR-006 — Observable resolution pipeline

## Status

Proposed

## Context

The project now follows a canonical model + Generic Integration Gateway + Provider Gateway architecture. PR5 moved Apple Music delivery behind a dedicated provider gateway and introduced IdentityCache-backed resolution.

Real E2E tests showed that the pipeline is stable but still too opaque: a track can be reported as `NOT_FOUND` without explaining whether Music.app returned no candidates or whether candidates were rejected by scoring.

A sustainable multi-provider architecture needs an observable resolution pipeline. Each provider can keep its own technical discovery strategy, but the application must receive canonical outcomes with diagnostics.

## Decision

Add a provider-local diagnostic model for Apple Music resolution:

- `AppleMusicResolutionTrace`
- `AppleMusicQueryTrace`
- candidate counts
- best score
- cache-hit visibility
- accepted candidate reference
- human-readable summary

Keep the trace inside the Apple Music provider boundary. The canonical model remains provider-neutral.

Also expand query generation from strict title/artist variants to progressive discovery variants:

1. title + artist
2. artist + title
3. title
4. title keyword variants
5. artist
6. artist keyword variants
7. contextual aliases
8. section hints

The provider still performs final selection through the shared scoring engine.

## Consequences

Positive:

- Failed imports become explainable.
- Future UI can surface ambiguous matches and rejected candidates.
- IdentityCache behavior becomes visible.
- Apple Music remains isolated as a Provider Gateway.
- The same diagnostic pattern can be reused by Spotify, MusicKit or other providers.

Trade-offs:

- More AppleScript search variants can make resolution slightly slower.
- More diagnostics means more internal data to maintain.

The trade-off is accepted because playlist generation is not latency-critical, while correctness and maintainability are critical.

## Next steps

- Add a richer text/JSON diagnostic report for resolver traces.
- Add a catalogue fallback provider when Music.app local library returns no candidates.
- Introduce a generic `ResolutionTrace` contract once a second provider exists.
