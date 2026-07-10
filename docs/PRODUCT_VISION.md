# Product Vision

## One sentence

**Resonance helps you compose and own your playlists locally, then synchronize them with the music services you already pay for — without locking you into one vendor.**

## Problem

Creating and maintaining playlists across streaming services is tedious:

- Manual track-by-track editing does not scale.
- Each service has its own library, UI, and limits.
- "Smart" playlists inside services optimize for engagement, not your intent.
- Export/import between services is fragile or impossible.

## Solution

Resonance provides three layers:

```text
┌─────────────────────────────────────────┐
│  Resonance app (macOS) + future iOS     │  ← Product experience
├─────────────────────────────────────────┤
│  Python engine                          │  ← Generation, import, sync
│  · Composition & scoring                │
│  · Local playlist repository (SSOT)     │
│  · Provider-neutral sync engine         │
├─────────────────────────────────────────┤
│  Provider gateways                      │  ← Apple Music, YouTube, …
└─────────────────────────────────────────┘
```

## Principles

| Principle | Meaning |
|-----------|---------|
| **Local-first** | Your playlists live on your machine. Works offline for editing. |
| **Provider-neutral core** | The engine never hardcodes Apple, Spotify, or YouTube. |
| **Non-destructive by default** | Create and update; never silently delete provider playlists. |
| **No account required** | Full functionality without Resonance cloud. |
| **Musical freedom** | No imposed genre or mood — your seeds, your rules. |
| **Gratuit d'abord** | Free CLI path remains; no paid license to use the engine. |

## Users

| Persona | Need |
|---------|------|
| **Casual listener** | "Make me a 4-hour pool party playlist" |
| **Curator** | Fine control over sections, energy, exclusions |
| **Multi-service user** | Same playlist logic across Apple Music and YouTube |
| **Developer** | Extend providers, automate via CLI |

## What Resonance is not

- Not a music player or streaming service
- Not a replacement for Apple Music / Spotify subscriptions
- Not a cloud music locker
- Not a social playlist network (today)

## Relationship to CLI legacy

The project began as an **Apple Music playlist builder CLI**. That path remains supported. Resonance is the **product evolution** — same engine, broader ambition.

## Future: Resonance Services (optional)

A future optional account may sync **metadata** (preferences, AI profile, playlist copies) across your devices — never audio, never provider tokens. Documented in [ADR-013](architecture/ADR-013-multi-provider-platform-vision.md). Not implemented.

## Further reading

- French user narrative: [wiki/Vision-et-Objectif.md](../wiki/Vision-et-Objectif.md)
- Technical architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Provider strategy: [PROVIDER_PLATFORM.md](PROVIDER_PLATFORM.md)
