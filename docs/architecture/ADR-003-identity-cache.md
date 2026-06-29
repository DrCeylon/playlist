# ADR-003: Cross-provider identity cache

- **Status:** Accepted
- **Date:** 2026-06-29
- **Depends on:** ADR-001, ADR-002

## Context

Resolution currently repeats provider lookups for the same canonical track. At scale
with 10 providers and large playlists, this creates avoidable latency and API load.

We need a provider-neutral cache mapping:

```text
CanonicalTrack.identity_key → ProviderIdentity(external_id, confidence, resolved_at)
```

## Decision

Introduce:

| Component | Location | Role |
|-----------|----------|------|
| `ProviderIdentity` | `canonical/models.py` | Value object for resolved provider IDs |
| `JsonCache` | `infrastructure/cache/store.py` | Generic JSON persistence |
| `IdentityCache` | `infrastructure/cache/identity_cache.py` | Canonical ↔ provider mapping |
| Key helpers | `infrastructure/cache/keys.py` | Namespaced cache keys |

`catalog/cache.py` becomes a backward-compatible facade over `JsonCache`.

### Key format

```text
identity::{provider_id}::{canonical_track_identity_key}
catalog::{provider_id}::{namespace}::{key}
```

Namespaces prevent collisions between identity cache, catalog search cache, and
future provider-specific caches in a single JSON file if desired.

## Consequences

### Positive

- Resolution can short-circuit on cache hits (PR 5)
- One persistence primitive (`JsonCache`) for all cache types
- Provider IDs are explicit via `ProviderId` enum

### Trade-offs

- Existing iTunes cache keys (`itunes::...`) remain until catalog gateway migration (PR 4)
- Identity and catalog caches may share a file path but use distinct key namespaces

## Follow-up

- PR 4: migrate `AppleCatalogSearch` to `catalog_entry_key()`
- PR 5: use `IdentityCache` in delivery/resolution pipeline
