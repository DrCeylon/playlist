# ADR-005: Apple Music delivery gateway and identity-cache resolution

- **Status:** Accepted
- **Date:** 2026-06-29
- **Depends on:** ADR-001, ADR-002, ADR-003, ADR-004

## Context

Playlist delivery (`create_playlist.py`) still relied on legacy `MusicClient` with
embedded AppleScript resolution logic. Python scoring (`select_best_resolution`) was
not used during library lookup, and `IdentityCache` was unused despite being available.

The E2E flow for a simple track (`Kygo - Firestone`) failed at delivery with
`Non trouvés: 1` even though generation and JSON export worked correctly.

## Decision

Introduce an Apple Music delivery + resolution pipeline under `integration/apple_music/`:

| Component | Location | Role |
|-----------|----------|------|
| `AppleScriptClient` | `applescript_client.py` | Technical AppleScript adapter (search, add by persistent ID) |
| `AppleMusicResolver` | `resolver.py` | IdentityCache lookup + candidate collection + unified scoring |
| `AppleMusicDelivery` | `delivery.py` | Playlist sync/incremental import |
| `AppleMusicImportService` | `import_service.py` | Orchestrates resolution then delivery |
| `IntegrationGateway` | `integration/gateway/service.py` | Routes canonical imports to provider gateways |
| `MusicClient` | `music/client.py` | Backward-compatible facade over import service |

### Pipeline

```text
CanonicalPlaylist
  → IntegrationGateway
    → AppleMusicProviderGateway
      → AppleMusicImportService
        → IdentityCache lookup (per CanonicalTrack.identity_key)
        → AppleScript candidate collection (if cache miss)
        → select_best_resolution (MIN_ACCEPTABLE_SCORE)
        → IdentityCache save on success
        → AppleMusicDelivery (add by persistent ID)
  → CanonicalImportReport
  → legacy TrackAddResult (CLI compatibility)
```

### Design rules

- `persistent_id` never enters `CanonicalTrack`; it lives in `ProviderIdentity.external_id`
  and `CanonicalCandidate.provider_hints`.
- AppleScript collects candidates only; Python scores and decides.
- Query variants include title+artist, title-only, and artist-only searches.
- `MusicClient` remains for CLI compatibility but delegates to the new pipeline.

## Consequences

### Positive

- Provider-specific delivery logic is isolated and testable without macOS
- Repeat imports benefit from `IdentityCache` short-circuit
- Unified scoring prevents blind acceptance of weak Apple Music matches
- Generic `IntegrationGateway` is ready for additional providers

### Trade-offs

- Two-phase AppleScript (collect candidates, then add by ID) vs. old single-script resolve
- `LibraryResolvePort` is not yet a separate class; resolver logic lives in `AppleMusicResolver`
- Real E2E still requires macOS + Music.app + library containing the track

### AppleScript limitations

- Depends on Music.app local library content (subscription tracks may not be in library)
- Fragile output parsing mitigated via `FIELD_DELIMITER`, `CANDIDATE_DELIMITER`, `RESULT_DELIMITER`
- Music not running yields controlled `ERROR` outcomes, not crashes

## Follow-up

- PR 6: Application layer reorganization
- PR 7: Wire `ProviderGatewayRegistry` through all entry points
- PR 8: Remove legacy resolver shims once all callers use `integration/`
- Optional: explicit `LibraryResolvePort` adapter wrapping `AppleMusicResolver`
- Optional: catalog-assisted fallback when library search returns no candidates

## Adding Spotify later

Implement `integration/spotify/` with the same ports:
`Resolver` + `Delivery` + `ImportService`, register in `ProviderGatewayRegistry`.
The application continues to pass `CanonicalPlaylist` — no Spotify types in core.
