# Phase 5 — Vision produit (proposition)

*Réflexion stratégique — pas d'implémentation dans cette phase.*

## Contexte

Les Phases 4.0–4.8A, **5.1** et **5.1.1** ont livré un **MVP macOS fonctionnel** : génération, import Apple Music (progression live, deep links Music), historique, diagnostics, thèmes, **Smart Input**. Les prochaines étapes (5.2+) transforment Resonance en **produit quotidien**.

→ [État des phases](Etat-des-Phases)

## Vision

**Resonance devient l'outil de référence pour créer et maintenir des playlists intelligentes sur Apple Music** — avec la même puissance que la CLI, mais sans friction.

## Axes prioritaires

### 1. Produit — « Finir le cycle »

| Fonctionnalité | Pourquoi |
|----------------|----------|
| **Édition playlist post-import** | Ajouter/retirer/réordonner sans repasser par zéro |
| **Templates & presets** | Réutiliser Orlando Pool Party, profils énergie |
| **Import incrémental** | `sync=False` bridge — ajouter morceaux sans tout effacer |
| **File d'attente import** | Plusieurs playlists en série |

### 2. UX — « Sensation produit »

- Onboarding premier lancement (autorisations Automatisation)
- Empty states soignés (historique vide, pas de bridge)
- Feedback haptique/sonore optionnel sur succès import
- Raccourcis clavier macOS (⌘G générer, ⌘I importer)
- Mode sombre/clair synchronisé avec système

### 3. Technique — « Fondations solides »

| Évolution | Bénéfice |
|-----------|----------|
| `ImportCoordinator` partagé | Historique + builder = même UX import |
| Bridge `AsyncStream` | Swift 6 propre, moins de jank MainActor |
| `ResonanceCoreTests` dédié | Tests bridge hors ResonanceMac |
| CI macOS (GitHub Actions) | `swift test` automatique |
| Profiling import | Identifier goulots Music.app vs bridge |

### 4. Apple Music — « Fiabilité »

- Diff sync vs full replace dans l'UI
- Carte manuelle dans réimport historique
- Skip morceau / ignorer acquisition
- Rapport export PDF/HTML depuis l'app

### 5. iOS — « Première pierre » (optionnel Phase 5b)

- Package `ResonanceIOS` shell lecture seule
- Pas d'import Apple Music sur iOS (contrainte plateforme)
- Preview + partage playlist JSON

## Risques

| Risque | Mitigation |
|--------|------------|
| Music.app instable | Conserver pacing/retry ; ne pas saturer AppleScript |
| Scope creep | Découper 5.1.1 (import UX) / 5.2 (édition) / 5.3 (CI+) |

## Phase 5.1 — livrée

Smart Input Framework mergé (PR #33). Voir [Phase 5.1 — Smart Input](Phase-5-1-Smart-Input) et [Smart Input Framework](Smart-Input-Framework).

## Phase 5.1.1 — livrée

UX import Apple Music mergée (PR #36) : progression morceau par morceau, texte sélectionnable, deep links Music, sonde bibliothèque. Voir [Phase 5.1.1 — Import UX](Phase-5-1-1-Import-UX).
| Dette bridge | Refactor AsyncStream avant nouvelles commandes |
| iOS trop tôt | Valider macOS production d'abord |

## Phase 5.2 — validée fonctionnellement

Voir [Phase 5.2 — Clôture](Phase-5-2-Cloture) et [État des phases](Etat-des-Phases).

## Phase 5.3 — performance (prochaine)

Voir [Phase 5.3 — Performance](Phase-5-3-Performance) : mesure import/génération, bridge, cache, hypothèses AppleScript vs MusicKit.

## Dépendances

- Validation utilisateur Phase 4.8A sur Mac réel
- Merge stable `main`
- Wiki à jour (cette clôture)

## Critères de succès Phase 5

1. Un utilisateur crée, importe, retrouve et **modifie** une playlist sans la CLI
2. `swift test` vert en CI macOS
3. Temps import 50 morceaux < perception « acceptable » (< 3 min typique)
4. Zéro message d'erreur Cocoa brut côté utilisateur

## Ce qu'on ne fait PAS en Phase 5

- Spotify / multi-provider UI (reste architecture-ready)
- MusicKit production (reste expérimental CLI)
- Suppression playlist/bibliothèque (principe non destructif)

---

*Proposition à affiner avec retours utilisateur post-4.8A.*
