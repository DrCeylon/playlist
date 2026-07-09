# ADR-018 — Experimental YouTube Music Gateway

## Status

Proposed — Phase 6.6

## Context

Product requires YouTube Music for provider comparison. No official consumer playlist API exists. Community libraries (e.g. **ytmusicapi**) use undocumented endpoints and browser authentication.

## Decision

### Positioning

- YouTube Music is **experimental only** (`ProviderCapability.EXPERIMENTAL`, `is_experimental=true`)
- Never the default provider for generation or import delivery
- Apple Music remains production path for `ProviderImportPort`

### Implementation boundary

```
playlist_builder/integration/youtube_music/
  __init__.py          # register only if extra installed
  gateway.py           # YouTubeMusicProviderGateway
  auth.py              # ProviderAuthPort — cookie file path, not embedded secrets
  read_port.py         # ProviderPlaylistReadPort — best effort
  experimental_guard.py # runtime checks + user disclaimer flag
```

### Dependency policy

- **Not** in `requirements.txt` / core `pyproject.toml dependencies`
- Optional extra: `pip install playlist-builder[youtube]` → adds `ytmusicapi` (pinned)
- CI: tests use mocks; integration tests `pytest.mark.skip` without `YOUTUBE_TEST_HEADERS`

### Auth model

1. User exports browser headers / oauth JSON to a **local file** (documented)
2. `ProviderAuthPort.connect` validates file readable — stores path in Keychain reference, not content in logs
3. On failure → `auth_state=error`, UI suggests **Import fichier JSON/CSV**

### Read scope v1

- List user playlists (if auth works)
- Get playlist tracks
- **No write port** in v1

### Legal / product

- UI disclaimer: unofficial API, may break, user responsible for ToS compliance
- No scraping of DRM streams — metadata only

### Fallback path (always available)

`ImportRemotePlaylistFromFile` use case:

- Parse export JSON/CSV → `RemotePlaylistSnapshot`
- Same downstream as API read — no YouTube code in Core

## Consequences

### Positive

- Compare Apple vs YouTube via local snapshots without blocking on API stability
- Production users unaffected if extra not installed

### Negative

- Maintenance burden when ytmusicapi breaks
- Support limited for auth issues

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Official API | Does not exist for playlists |
| Hard dependency ytmusicapi | Breaks reproducible core install |
| Skip YouTube entirely | Product requires comparison path |

## References

- ADR-014, ADR-015, ADR-017
- `docs/TECHNICAL_DEBT.md` (gateway YouTube item)
- `docs/product/phase-6-provider-platform.md`
