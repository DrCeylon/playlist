# ADR-015 — Provider Authentication Boundary

## Status

Accepted — Phase 6.1; extended July 2026 to distinguish provider auth from Resonance Identity (docs only).

## Context

Real playlist read/sync requires per-provider authentication:

- **Apple Music:** Music.app / library access (macOS runtime — largely implicit)
- **YouTube Music:** OAuth cookies or browser session (experimental)
- **Spotify (future):** OAuth 2.0 PKCE

Secrets must never flow through bridge logs, session history, or git.

**Distinction:** `ProviderAuthPort` authenticates **Music Providers** (Apple Music runtime, Spotify OAuth, YouTube cookies). A future **Resonance Identity** service authenticates the optional Resonance account — separate ports, separate Keychain entries, separate UI flows. The Resonance account is **not** a music provider and must not appear in `ProviderOption` as a streaming source.

## Decision

### Port

```python
@runtime_checkable
class ProviderAuthPort(Protocol):
    @property
    def provider_id(self) -> ProviderId: ...

    def auth_state(self) -> ProviderAuthState: ...

    def connect(self, *, params: dict[str, str]) -> ProviderAuthState: ...

    def disconnect(self) -> ProviderAuthState: ...
```

`ProviderAuthState`: `disconnected | configured | connected | expired | error | experimental_unavailable`

### Storage boundary

| Data | Storage |
|------|---------|
| OAuth tokens, cookies (music providers) | macOS Keychain (Swift) or encrypted file outside repo |
| Display name, expiry metadata | `RemoteProviderAccount` in local config store |
| Bridge payloads | **Never** include secrets — only `auth_state` enum + masked labels |
| Resonance Identity tokens (future) | Separate Keychain namespace — never mixed with provider OAuth |
| Cloud-synced metadata (future) | Encrypted at rest on Resonance backend — **no audio blobs** |

### Principles

- All app features work **without** a Resonance account; provider auth is per music service only.
- Music provider OAuth remains **local-first** (Keychain on device).
- Resonance Cloud Sync (future) replicates **metadata** (playlists gérées, exclusions, préférences IA) — not provider secrets, not music files.

### UI boundary

- `ProvidersView` triggers connect/disconnect via bridge commands `provider_auth_status`, `provider_connect`, `provider_disconnect`
- Experimental providers show disclaimer before connect

### Apple Music special case

`connected` when Music.app runtime reachable (`ProviderImportPort.ensure_runtime_ready` pattern reused at gateway level, not duplicated in UI).

## Consequences

- Auth logic isolated per `integration/<provider>/auth.py`
- Tests use in-memory `ProviderAuthPort` fakes
- YouTube connect optional — app remains usable without it

## Non-goals

- Centralized OAuth server for music providers
- Storing credentials in Python session history JSON
- Resonance Identity login implementation (future phase)
- Using Resonance account as substitute for Spotify/Apple authentication

## References

- ADR-014, ADR-018
- `docs/product/phase-6-provider-platform.md`
