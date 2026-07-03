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
| **5.1** | Smart Input Framework (autocomplete, refs canoniques) | PR #33 @ `99e269d` |

## En cours (PR ouvertes)

| PR | Branche | Sujet | Statut |
|----|---------|-------|--------|
| [#35](https://github.com/DrCeylon/playlist/pull/35) | `cursor/track-autocomplete-artist-filter-ef21` | Filtre morceaux par artiste sélectionné | Brouillon |
| [#36](https://github.com/DrCeylon/playlist/pull/36) | `cursor/phase-5-1-1-import-ux-ef21` | UX import Apple Music (progression live, Music deep links) | Brouillon |

## Récemment mergées

| PR | Sujet | Merge |
|----|-------|-------|
| [#34](https://github.com/DrCeylon/playlist/pull/34) | Icône Dock 1024×1024 transparente | Juillet 2026 |
| [#37](https://github.com/DrCeylon/playlist/pull/37) | Maintenance dépôt post Phase 5.1 | Juillet 2026 |

## Prochaines étapes envisagées

| Phase | Thème | Référence |
|-------|-------|-----------|
| **5.1.1** | Import UX (merge PR #36) | `Phase-5-1-1-Import-UX.md` sur branche feature |
| **5.2+** | Édition playlist, templates, `ImportCoordinator` | [Phase 5 — Vision](Phase-5-Vision) |

## Branches Git actives

Seules ces branches existent sur `origin` :

- `main` — branche par défaut, protégée par convention
- `cursor/*-ef21` — une branche par PR active (suffixe `-ef21` obligatoire pour les agents Cursor)

Les anciennes branches Cursor (Phases 4.x) ont été supprimées après merge.

## Validation qualité (`main`)

```bash
python3 -m pytest -q
cd apps/resonance && ./scripts/build.sh   # macOS uniquement
```

~318 tests Python sur Linux ; build + `swift test` sur macOS (CI `resonance-macos.yml`).
