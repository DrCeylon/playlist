# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `main` branch | ✅ Active development |
| Tagged releases | ✅ When published |

## Reporting a vulnerability

**Please do not open public GitHub issues for security vulnerabilities.**

Report privately via [GitHub Security Advisories](https://github.com/DrCeylon/playlist/security/advisories/new).

Include:

- Description of the issue and potential impact
- Steps to reproduce
- Affected components (Python engine, macOS app, bridge, provider integration)
- Suggested fix if you have one

We aim to acknowledge reports within **7 days** and provide a status update within **30 days**.

## Security model (summary)

| Asset | Handling |
|-------|----------|
| Provider OAuth / cookies | Local device only — Keychain or user-managed header files (YouTube experimental) |
| Bridge payloads | Must not contain raw credentials — enforced by `assert_bridge_safe_mapping` |
| Playlist data | Local JSON repository — no cloud upload by default |
| Resonance account | Not implemented — no central auth surface |

See [ADR-015](docs/architecture/ADR-015-provider-auth-boundary.md) for provider authentication boundaries.

## Out of scope

- Social engineering against music provider accounts
- Vulnerabilities in Apple Music, YouTube, or other third-party services
- Issues requiring physical access to an unlocked machine

## Safe harbor

We support good-faith security research on this repository. Do not access other users' data, disrupt services, or violate applicable laws.
