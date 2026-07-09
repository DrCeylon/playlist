# État des phases (juillet 2026)

Tableau de référence pour l'avancement du projet Resonance / playlist-builder.

## Phases terminées (mergées sur `main`)

| Phase | Contenu | Merge |
|-------|---------|-------|
| **1** | Fondations CLI, JSON playlist, Apple Music | Historique |
| **2** | Génération intelligente (seeds, énergie, scoring) | PR #5, #8 |
| **3** | Gateway enterprise, intégration Apple Music | PR #17 |
| **4.0–4.3** | Discovery UI, DTO, bridge, thèmes | PR #18–#21 |
| **4.4–4.5** | Shell macOS, formulaire playlist | PR #22–#23 |
| **4.6** | Bridge runtime, import streaming | PR #26 |
| **4.7** | Laboratoire diagnostics | PR #27 |
| **4.7a–4.7b** | Excellence Swift, environnement reproductible | PR #29–#31 |
| **4.8** | Historique sessions | PR #30 |
| **4.8A** | Stabilisation UX macOS, thèmes, import | PR #32 |
| **5.1** | Smart Input Framework (autocomplete, refs canoniques) | PR #33 |
| **5.1.1** | UX import Apple Music (progression live, Music deep links, acquisition auto) | PR #36 |
| **5.2–5.5** | Workflow coordinator, historique live, ProviderImportPort, acquisition manuelle SSOT | `main` |
| **Playlist Manager** | Dashboard, Playlists / Sync / Providers, DTO library, YouTube expérimental | Tag `phase-playlist-manager-complete` — [clôture](Phase-Playlist-Manager-Cloture) |

Correctifs intégrés sur `main` :

| PR | Sujet |
|----|-------|
| [#34](https://github.com/DrCeylon/playlist/pull/34) | Icône Dock 1024×1024 transparente |
| [#35](https://github.com/DrCeylon/playlist/pull/35) | Filtre autocomplete morceaux par artiste sélectionné |
| [#37](https://github.com/DrCeylon/playlist/pull/37) | Maintenance dépôt (Package.swift, workflow Git) |

## État courant (`main`)

- **401** tests Python (`pytest -q`), **1** skipped (Swift build sur macOS uniquement)
- App macOS : génération, import robuste, historique, **gestionnaire de playlists** (preview)
- Détail : [Phase Playlist Manager — clôture](Phase-Playlist-Manager-Cloture)

## Prochaine phase

| Phase | Thème | Référence |
|-------|-------|-----------|
| **Sync réelle / YouTube gateway** | Pull provider, tracks historiques | [Dette technique](../docs/TECHNICAL_DEBT.md) |
| **5.4+** | Édition playlist, templates, polish UI | [Phase 5 — Vision](Phase-5-Vision) |

## Branches Git

Sur `origin` : **`main`** + branches `cursor/*` résiduelles (docs, dev env, tests isolés) — voir [Dette technique](../docs/TECHNICAL_DEBT.md).

Les branches feature mergées sont supprimées après fast-forward ou squash.

## Validation qualité (`main`)

```bash
python3.12 -m pytest -q
cd apps/resonance && swift build && swift test && ./scripts/build.sh
```

401 tests Python ; `swift build` + `swift test` sur macOS (CI `resonance-macos.yml`).
