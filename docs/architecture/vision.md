# Architecture vision

> **Plugin platform:** [PLUGIN_PLATFORM_AUDIT.md](../PLUGIN_PLATFORM_AUDIT.md) · [ADR-020](ADR-020-plugin-platform-foundations.md)

## Goal

Build a multi-provider playlist composition and delivery platform that can integrate
at least ten music providers over the next five years without rewriting the core
application.

The product is organized around three bounded contexts:

1. **Composition** — turn user intent (seeds, keywords, constraints) into a canonical playlist.
2. **Catalog** — discover and rank musical candidates from external sources.
3. **Delivery** — resolve canonical tracks to provider identities and import playlists.

## Layering

```text
UI / CLI
   ↓
Application (use cases)
   ↓
Canonical model + contracts (ports)
   ↓
Generic Integration Gateway
   ↓
Provider Gateways (Apple, Spotify, …)
   ↓
External platforms
```

## Dependency rule

Dependencies always point inward.

- `canonical/` imports nothing from application or integration code.
- Application code imports `canonical/` and ports, never AppleScript or Spotify URIs.
- Provider gateways implement ports and own all platform-specific models.

## Canonical model

The canonical model describes musical identity and playlist structure using
provider-neutral vocabulary:

- `CanonicalTrack`, `CanonicalArtist`, `CanonicalAlbum`
- `CanonicalPlaylist`, `CanonicalCandidate`, `CanonicalResolution`
- `ProviderId`, `ImportStatus`, `ResolutionDecision`

Provider identifiers (Apple persistent IDs, Spotify URIs, MusicKit song IDs) never
appear in canonical types. They belong to integration adapters and the identity cache.

## Integration gateway pattern

Each provider implements a `ProviderGateway` exposing zero or more capabilities:

- `catalog` — external catalog search
- `library` — resolve against a user's library
- `delivery` — create or synchronize playlists

The generic gateway orchestrates provider selection, mapping, caching, and error
normalization. Adding a provider means registering a new gateway implementation,
not changing composition or delivery use cases.

## Resolution pipeline (target)

```text
Search → Collect candidates → Normalize → Score → Confidence → Decision → Import
```

Platform code is responsible for candidate collection only. Scoring and decisions
remain in Python so they are deterministic, testable, and provider-agnostic.

## Engineering standards

- Python 3.12+
- stdlib first; new dependencies require justification
- `Protocol` ports instead of deep inheritance trees
- frozen dataclasses with `slots=True` for canonical value objects
- incremental PRs; no big-bang rewrites

## Success criteria

- Zero Apple-specific imports outside integration packages
- 100% unit test coverage for new canonical and scoring modules
- Existing CLI workflows remain backward compatible during migration
- A new provider can be bootstrapped with gateway + mapper + tests only
