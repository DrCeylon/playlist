# ADR-004: Apple Music catalog provider gateway

- **Status:** Accepted
- **Date:** 2026-06-29
- **Depends on:** ADR-001, ADR-002, ADR-003

## Context

Catalog discovery was tightly coupled to `planning.CandidateTrack` and the legacy
`AppleCatalogSearch` class. iTunes HTTP details, cache keys, and discovery scoring
lived in the same module graph as playlist planning.

To support multiple providers (Spotify, Deezer, …) we need:

1. A provider-neutral discovery model (`DiscoveryCandidate`)
2. A canonical catalog port (`CatalogSearchPort`)
3. An Apple-specific integration package under `integration/`
4. Namespaced catalog cache keys with legacy fallback

## Decision

Introduce the Apple Music integration layer:

| Component | Location | Role |
|-----------|----------|------|
| `DiscoveryCandidate` | `discovery/models.py` | Provider-neutral discovery result |
| `ITunesSearchClient` | `integration/apple_music/itunes_client.py` | Low-level iTunes Search API + cache |
| `AppleCatalogGateway` | `integration/apple_music/catalog_gateway.py` | `CatalogSearchPort` implementation |
| `AppleMusicProviderGateway` | `integration/apple_music/gateway.py` | `ProviderGateway` façade |
| `ProviderGatewayRegistry` | `integration/gateway/registry.py` | Registry stub for PR 7 |
| Mapper helpers | `integration/apple_music/mapper.py` | Canonical ↔ discovery ↔ legacy mapping |

### Boundary rules

- Discovery providers return `DiscoveryCandidate`, never `CandidateTrack`.
- Planning adaptation happens in `discovery/adapters.py` at the pipeline boundary.
- `AppleCatalogSearch` remains a backward-compatible facade over the new gateway.
- Cache keys use `catalog::apple_music::...` with read fallback to legacy `itunes::...`.

### Data flow

```text
PlaylistRequest
  → DiscoveryPipeline
    → ITunesCandidateProvider (CatalogSearchPort)
      → AppleCatalogGateway
        → ITunesSearchClient
  → DiscoveryCandidate pool (dedupe by identity_key)
  → discovery/adapters → CandidateTrack
  → PlaylistPlanner
```

## Consequences

### Positive

- Discovery is decoupled from planning types
- Apple HTTP and cache logic are isolated for future provider parity
- ADR-003 namespaced cache keys are adopted for catalog search
- `generate_playlist.py` wires the gateway directly (facade optional)

### Trade-offs

- Extra conversion step between discovery and planning
- `ProviderGatewayRegistry` is minimal until PR 7
- Legacy `itunes::` cache entries remain readable but new writes use namespaced keys

## Follow-up

- PR 5: Apple delivery + resolution pipeline using `IdentityCache`
- PR 7: wire `ProviderGatewayRegistry` through application entry points
- PR 8: remove legacy shims once all callers use `integration/`
