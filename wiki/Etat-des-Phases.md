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

## PR ouvertes

Aucune — toutes les PR actives de juillet 2026 ont été mergées.

## Prochaines étapes envisagées

| Phase | Thème | Référence |
|-------|-------|-----------|
| **5.2+** | Édition playlist, templates, `ImportCoordinator` | [Phase 5 — Vision](Phase-5-Vision) |

## Branches Git

Sur `origin` : **`main` uniquement**.

Les branches feature `cursor/*-ef21` sont supprimées après chaque merge squash.

## Validation qualité (`main`)

```bash
python3 -m pytest -q
cd apps/resonance && ./scripts/build.sh   # macOS
```

323 tests Python (1 skipped hors macOS) ; `swift build` + `swift test` sur macOS (CI `resonance-macos.yml`).
