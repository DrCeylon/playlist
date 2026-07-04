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

| PR | Branche | Sujet | Statut |
|----|---------|-------|--------|
| [#39](https://github.com/DrCeylon/playlist/pull/39) | `cursor/phase-5-2-generation-import-ux-ef21` | Phase 5.2 — génération complète, import performant, UX exclusions, historique workflow, bandeau processus | **Draft** — validation macOS requise avant merge |
| [#38](https://github.com/DrCeylon/playlist/pull/38) | `cursor/phase-5-1-2-product-ux-stabilization-ef21` | Phase 5.1.2 — stabilisation UX produit (intégrée en grande partie dans 5.2) | Draft — à fermer après merge #39 |

## Phase 5.2 — en cours (PR #39)

Livrables UX principaux :

| Fonctionnalité | Comportement |
|----------------|--------------|
| **Historique = reprise workflow** | Panneau droit réutilise `PlaylistPreviewView` / `ImportReportView` selon le statut session ; actions techniques réservées au mode Architecte |
| **Bandeau processus global** | Génération ou import en cours visible depuis tout l'écran ; clic → retour au workflow actif ; couleur `statusInfo` dédiée |
| **`AppWorkflowCoordinator`** | ViewModels partagés (builder, import, smart input) ; pas de relance bridge au retour d'écran |
| **Statuts FR** | Générée, Importée, Partielle, Échec dans la liste historique |

Validation attendue sur macOS :

```bash
cd apps/resonance
swift build && swift test && ./scripts/build.sh
cd ../..
python3 -m pytest -q
```

## Prochaines étapes envisagées

| Phase | Thème | Référence |
|-------|-------|-----------|
| **5.2 merge** | Clôture PR #39 après validation Mac | Cette PR |
| **5.3+** | Édition playlist, templates, `ImportCoordinator` affiné | [Phase 5 — Vision](Phase-5-Vision) |

## Branches Git

Sur `origin` : **`main`**, **`cursor/phase-5-2-generation-import-ux-ef21`** (PR #39), **`cursor/phase-5-1-2-product-ux-stabilization-ef21`** (PR #38 draft).

Les branches feature `cursor/*-ef21` sont supprimées après chaque merge squash.

## Validation qualité (`main`)

```bash
python3 -m pytest -q
cd apps/resonance && ./scripts/build.sh   # macOS
```

323 tests Python (1 skipped hors macOS) ; `swift build` + `swift test` sur macOS (CI `resonance-macos.yml`).
