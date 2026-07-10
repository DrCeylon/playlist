# Roadmap

High-level direction for Resonance. Detailed phase history: [wiki/Etat-des-Phases.md](../wiki/Etat-des-Phases.md).

## Vision (north star)

A **local-first playlist studio** that works with any music service you already use — compose intelligently, keep control locally, sync when you choose.

## Shipped (foundation complete)

| Capability | Status |
|------------|--------|
| Intelligent playlist generation (seeds, energy, scoring) | ✅ |
| Apple Music catalog, library, delivery | ✅ |
| macOS Resonance app (generate, import, history, themes) | ✅ |
| Local managed playlist repository (SSOT) | ✅ |
| Provider-neutral sync (plan, apply, conflicts) | ✅ |
| YouTube Music experimental (read, auth, file import) | 🧪 |

## Near term (open for contributors)

| Item | Area | Notes |
|------|------|-------|
| Sync UX wizard polish | Swift | Consume `resolve_sync_conflicts` in UI |
| Remote playlist browse UI | Swift + bridge | `list_remote_playlists` |
| Provider picker in generation | Swift | Remove Apple hardcode in ViewModel |
| Persistent bridge transport | Swift + Python | Reduce per-command process spawn |
| Domain DTO extraction | Python | Move types out of `ui/shared/dto` |
| SQLite repository option | Python | Scale beyond JSON files |
| Spotify gateway | Python | Read + auth skeleton |

## Medium term

| Item | Notes |
|------|-------|
| iOS app shell | Shared ResonanceCore |
| Mirror / reorder sync on Apple Music | After Music.app validation |
| YouTube Music write port | Only if technically reliable |
| Internationalization (i18n) | English + French message keys |
| Automated release tags & changelog | OSS hygiene |

## Long term (documented, not scheduled)

| Item | Reference |
|------|-----------|
| Resonance Identity / cloud metadata sync | ADR-013 § Resonance Services |
| AI-assisted playlist curation | Product vision |
| Additional providers (Deezer, Plex, …) | Provider platform |

## Explicit non-goals

- Hosting or streaming audio files
- Replacing music provider subscriptions
- Central OAuth broker for all providers
- Automatic conflict resolution without user consent (v1)

## How to propose roadmap changes

Open a GitHub Issue with the `enhancement` label or discuss in a PR that updates this file. Large items need an ADR.
