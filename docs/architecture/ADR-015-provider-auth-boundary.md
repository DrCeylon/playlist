# ADR-015 — Provider Authentication Boundary

## Status

Proposed — Phase 6.1

## Context

Real playlist read/sync requires per-provider authentication:

- **Apple Music:** Music.app / library access (macOS runtime — largely implicit)
- **YouTube Music:** OAuth cookies or browser session (experimental)
- **Spotify (future):** OAuth 2.0 PKCE

Secrets must never flow through bridge logs, session history, or git.

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
| OAuth tokens, cookies | macOS Keychain (Swift) or encrypted file outside repo |
| Display name, expiry metadata | `RemoteProviderAccount` in local config store |
| Bridge payloads | **Never** include secrets — only `auth_state` enum + masked labels |

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

- Centralized OAuth server
- Storing credentials in Python session history JSON

## References

- ADR-014, ADR-018
- `docs/product/phase-6-provider-platform.md`
