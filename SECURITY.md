# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `main` branch | Active development |
| `v1.0.x` tags | Security fixes when published |

## Reporting a vulnerability

**Do not open public GitHub issues for security vulnerabilities.**

Report privately via [GitHub Security Advisories](https://github.com/DrCeylon/playlist/security/advisories/new).

Include:

- Description and potential impact
- Steps to reproduce
- Affected components (Python engine, macOS app, bridge, provider integration)
- Suggested fix if available

We aim to acknowledge reports within **7 days** and provide a status update within **30 days**.

## Security model (summary)

| Asset | Handling |
|-------|----------|
| Provider OAuth / cookies | Local device only — Keychain or user-managed files (YouTube experimental) |
| Bridge payloads | Must not contain raw credentials — `assert_bridge_safe_mapping` |
| Playlist data | Local JSON repository — no cloud upload by default |
| Resonance account | Not implemented in v1.0 |

See [ADR-015](docs/architecture/ADR-015-provider-auth-boundary.md).

## Out of scope

- Social engineering against music provider accounts
- Vulnerabilities in Apple Music, YouTube, or other third-party services
- Issues requiring physical access to an unlocked machine

## Safe harbor

Good-faith security research on this repository is welcome. Do not access other users' data, disrupt services, or violate applicable laws.
