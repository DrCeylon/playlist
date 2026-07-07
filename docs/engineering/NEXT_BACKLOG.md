# Next backlog

Backlog ordonné après stabilisation Phase 5.5. **Aucun item ci-dessous ne doit perturber la validation 5.5 en cours.**

---

## Immédiat — fin Phase 5.5

| ID | Item | Priorité | Notes |
|----|------|----------|-------|
| 5.5.7 | Build macOS 100 % vert | P0 | `swift build`, `swift test`, `./scripts/build.sh` |
| 5.5.8 | Merge `cursor/phase-5-5-validation` → `main` | P0 | Après revue utilisateur |
| 5.5.9 | Fermer / superseder PRs intermédiaires 5.5.x | P1 | Documentation PR |

---

## Phase 6.0 — Répertoire fondations (docs → code)

**Prérequis** : Phase 5.5 mergée sur `main`.  
**Spec** : [phase-6-repertoire.md](../product/phase-6-repertoire.md)  
**ADR** : ADR-014, ADR-015, ADR-016, ADR-017

| ID | Item | ADR | Notes |
|----|------|-----|-------|
| 6.0.1 | Modèles `SavedPlaylist`, `SavedPlaylistMetadata`, DTOs bridge | ADR-014 | Python `playlist_builder/repertoire/` + `ResonanceCore` |
| 6.0.2 | `PlaylistRepositoryPort` + persistance `data/repertoire/` | ADR-014 | Pattern identique à session history |
| 6.0.3 | Commandes bridge `list_repertoire`, `get_repertoire_playlist`, `save_to_repertoire`, `delete_repertoire_playlist` | ADR-014 | |
| 6.0.4 | `SidebarItem.repertoire`, `RepertoireView`, `RepertoireViewModel` | ADR-014 | Liste, ouvrir, supprimer |
| 6.0.5 | Raccourci Accueil → Répertoire | ADR-014 | Sans modifier autres écrans 5.5 |
| 6.0.6 | Tests architecture : Répertoire ≠ Historique | ADR-014 | |

**Hors périmètre 6.0** : publication provider, merge, inspiration IA, exports fichier.

---

## Phase 6.1 — Actions création

| ID | Item | ADR |
|----|------|-----|
| 6.1.1 | `BuilderEntryMode` + `loadFromSavedPlaylist()` | ADR-014, ADR-017 |
| 6.1.2 | Action Modifier → nouvelle playlist | ADR-017 |
| 6.1.3 | Action Créer une variation | ADR-017 |
| 6.1.4 | Auto-save / « Sauvegarder dans le Répertoire » post-génération | ADR-014 |
| 6.1.5 | Migration optionnelle Historique → Répertoire | ADR-014 |

---

## Phase 6.2 — Publication depuis Répertoire

| ID | Item | ADR |
|----|------|-----|
| 6.2.1 | `PlaylistPublication` + persistance | ADR-015 |
| 6.2.2 | `PlaylistPublicationPort` (compose `ProviderImportPort`, ne pas le modifier) | ADR-015 |
| 6.2.3 | `PlaylistPublicationViewModel` + `PlaylistPublishView` | ADR-015 |
| 6.2.4 | Bridge `publish_repertoire_playlist` | ADR-015 |

---

## Phase 6.3 — Filtres & fusion

| ID | Item | ADR |
|----|------|-----|
| 6.3.1 | `RepertoireFilterCriteria` + UI filtres | ADR-014 |
| 6.3.2 | `PlaylistMergeView` + `merge_repertoire_playlists` | ADR-017 |
| 6.3.3 | `PlaylistLineage` kind `mergedFrom` | ADR-017 |

---

## Phase 6.4 — Inspiration (stub IA)

| ID | Item | ADR |
|----|------|-----|
| 6.4.1 | `PlaylistInspirationPort` stub | ADR-017 |
| 6.4.2 | UI « Quelle source d'inspiration ! » | ADR-017 |
| 6.4.3 | Bridge `inspire_from_repertoire_playlist` | ADR-017 |

---

## Phase 6.5 — Exports

| ID | Item | ADR |
|----|------|-----|
| 6.5.1 | `PlaylistExportPort` | ADR-016 |
| 6.5.2 | Formats M3U, CSV, JSON | ADR-016 |
| 6.5.3 | Bridge `export_repertoire_playlist` | ADR-016 |

---

## Phase 6.6+ — Multi-provider publication

| ID | Item | Notes |
|----|------|-------|
| 6.6.1 | Publication Spotify | ADR provider-local à créer |
| 6.6.2 | Publication YouTube Music | ADR provider-local à créer |

---

## Dette / hors Phase 6

| ID | Item | Notes |
|----|------|-------|
| — | `ProviderImportPort` extraction complète | Phase 5.5+ (ADR-013) |
| — | Historique : recentrage audit pur | Après Répertoire 6.1 |
| — | Cross-device sync Répertoire | Hors scope v1 |
