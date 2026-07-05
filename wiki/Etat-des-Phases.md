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

Correctifs intégrés sur `main` :

| PR | Sujet |
|----|-------|
| [#34](https://github.com/DrCeylon/playlist/pull/34) | Icône Dock 1024×1024 transparente |
| [#35](https://github.com/DrCeylon/playlist/pull/35) | Filtre autocomplete morceaux par artiste sélectionné |
| [#37](https://github.com/DrCeylon/playlist/pull/37) | Maintenance dépôt (Package.swift, workflow Git) |

## Phase 5.2 — validée fonctionnellement (PR #39)

**Statut** : validée sur macOS — merge recommandé. Détail : [Phase 5.2 — Clôture](Phase-5-2-Cloture).

| PR | Branche | Tests macOS |
|----|---------|-------------|
| [#39](https://github.com/DrCeylon/playlist/pull/39) | `cursor/phase-5-2-generation-import-ux-ef21` | `swift build`, `swift test`, `./scripts/build.sh`, `pytest` 332 passed |

Livrables UX : workflow coordinator, historique live, bandeau processus, protection session active, import humanisé, instrumentation timings partielle.

**Limites acceptées (non bloquantes)** — voir [Phase 5.3 — Performance](Phase-5-3-Performance) :

- Polish textes / couleurs incomplet
- Import encore lent
- Génération ne remplit pas toujours le nombre de morceaux demandé
- Bridge Python one-shot par commande

| PR | Branche | Sujet | Statut |
|----|---------|-------|--------|
| [#38](https://github.com/DrCeylon/playlist/pull/38) | `cursor/phase-5-1-2-product-ux-stabilization-ef21` | Phase 5.1.2 — stabilisation UX produit (intégrée en grande partie dans 5.2) | Draft — à fermer après merge #39 |

## Prochaine phase

| Phase | Thème | Référence |
|-------|-------|-----------|
| **5.3** | **Performance** — mesure, import, génération, bridge, cache | [Phase 5.3 — Performance](Phase-5-3-Performance) |
| **5.4+** | Édition playlist, templates, polish UI | [Phase 5 — Vision](Phase-5-Vision) |

## Branches Git

Sur `origin` : **`main`**, **`cursor/phase-5-2-generation-import-ux-ef21`** (PR #39 prête merge).

Les branches feature `cursor/*-ef21` sont supprimées après chaque merge squash.

## Validation qualité (`main` + PR #39)

```bash
python3.12 -m pytest -q
cd apps/resonance && swift build && swift test && ./scripts/build.sh
```

332 tests Python ; `swift build` + `swift test` sur macOS (CI `resonance-macos.yml`).
