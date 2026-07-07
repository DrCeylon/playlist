# Phase 6 — Répertoire (bibliothèque de playlists)

**Statut** : conception — documentation uniquement, aucune implémentation  
**Prérequis** : Phase 5.5 stabilisée (validation `cursor/phase-5-5-validation`)  
**ADR associés** : ADR-014, ADR-015, ADR-016, ADR-017

## Vision produit

Faire évoluer Resonance d'un **assistant de création de playlist** vers un **gestionnaire de playlists multi-providers**.

Le **Répertoire** devient la bibliothèque permanente des playlists générées et l'écran principal d'exploitation. L'**Historique** reste un journal technique des workflows d'import/export.

### Règle non négociable

> Une playlist appartient au **Core** (`SavedPlaylist` / `CanonicalPlaylist`).  
> Les providers ne sont que des **destinations de publication**.  
> Le Répertoire ne dépend d'aucun provider.

Alignement : ADR-001 (modèle canonique), ADR-013 (Core = composition, providers = delivery).

---

## Parcours utilisateur

### Aujourd'hui

```text
Accueil → Nouvelle Playlist → Historique
```

L'Historique cumule deux rôles incompatibles : audit technique et pseudo-bibliothèque (reprise, modification du formulaire).

### Cible Phase 6

```text
Accueil
  → Nouvelle Playlist      (création)
  → Répertoire             (exploitation — écran principal)
  → Historique             (audit technique uniquement)
  → Laboratoire / Paramètres
```

| Zone | Rôle | Donnée source |
|------|------|---------------|
| **Répertoire** | Bibliothèque permanente des playlists générées | `SavedPlaylist` |
| **Historique** | Journal des exécutions (génération, import, erreurs, reprise manuelle) | `SessionHistoryRecord` (existant) |
| **Providers** | Destinations de publication uniquement | `PlaylistPublication` |

---

## Séparation des domaines

```text
┌─────────────────────────────────────────────────────────┐
│  Resonance Core (provider-neutral)                      │
│  SavedPlaylist · CanonicalPlaylist · GenerationRequest  │
└───────────────────────────┬─────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
   Répertoire          Historique         Publication
   (CRUD, filtres)     (audit, resume)    (provider dest.)
```

### Écart avec l'existant

| Concept actuel | Limite | Évolution Phase 6 |
|----------------|--------|-------------------|
| `SessionHistoryRecord` | Orienté session, pas curaté | Reste pour l'audit ; lien optionnel vers `SavedPlaylist` |
| `PlaylistGenerationResult` | Éphémère (ViewModel) | Contenu embarqué dans `SavedPlaylist` |
| `loadFromHistory()` | Historique comme pseudo-bibliothèque | `loadFromSavedPlaylist()` depuis le Répertoire |
| Import live | Seule « publication » | `PublishSavedPlaylist` via port dédié |

---

## Modèles métier (conception)

### `SavedPlaylist` — entité centrale

**Couche** : `ResonanceCore` (Swift) + `playlist_builder/repertoire/` (Python)  
**Persistance** : `data/repertoire/playlists.json` (enveloppe versionnée, pattern identique à l'historique)

| Champ | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Identifiant stable (≠ `session_id`) |
| `name` | `String` | Nom affiché |
| `description` | `String` | Description libre |
| `createdAt` / `updatedAt` | `ISO8601` | Horodatage |
| `generationRequest` | `PlaylistGenerationRequest` | Paramètres figés (seeds, keywords, énergie, exclusions, durée…) |
| `playlist` | `CanonicalPlaylist` (DTO) | Contenu musical provider-neutral |
| `metadata` | `SavedPlaylistMetadata` | Champs dérivés pour filtres |
| `lineage` | `PlaylistLineage?` | Provenance non versionnée (ADR-017) |
| `originSessionID` | `String?` | Lien optionnel vers la session d'historique créatrice |

**Invariants** :

- Aucun identifiant provider dans `SavedPlaylist`.
- `providerID` dans `generationRequest` = contexte de génération, pas propriété de la playlist.
- Modifier / Varier / S'inspirer → **nouvelle** `SavedPlaylist` ; l'originale reste immuable.

### `SavedPlaylistMetadata` — filtres

| Champ | Source |
|-------|--------|
| `trackCount` | `playlist.tracks.count` |
| `durationMs` | somme des `duration_ms` connues |
| `energyProfile` | `generationRequest.energyCurve.profile` |
| `keywords` | `generationRequest.keywords` |
| `genres` | union des genres des morceaux |
| `mood` | `String?` — réservé IA future |
| `seedArtist` / `seedTrack` | extraits des seeds |
| `averageScore` | score moyen de génération |

### `PlaylistLineage` — traçabilité sans versioning (ADR-017)

| Champ | Type |
|-------|------|
| `kind` | `.original` \| `.modifiedFrom` \| `.variationOf` \| `.mergedFrom` \| `.inspiredBy` |
| `sourcePlaylistIDs` | `[UUID]` |
| `note` | `String?` |

Pas de branche, pas de HEAD, pas de rollback.

### `PlaylistPublication` — publication provider (ADR-015)

Stockée dans `data/repertoire/publications.json`, séparée de `SavedPlaylist`.

| Champ | Description |
|-------|-------------|
| `playlistID` | Référence `SavedPlaylist` |
| `providerID` | Destination |
| `publishedAt` | Horodatage |
| `status` | `.published` \| `.partial` \| `.failed` |
| `externalReference` | ID opaque côté provider (hors Core) |
| `importSessionID` | Lien vers l'historique d'exécution |

Une même playlist peut avoir plusieurs publications (Apple, Spotify, etc.).

### `RepertoireFilterCriteria` — modèle de filtres (sans UI Phase 6.0)

```text
RepertoireFilterCriteria
├── searchText: String?
├── providerOrigin: ProviderID?       // contexte génération, pas publication
├── dateRange: ClosedRange<Date>?
├── trackCountRange: ClosedRange<Int>?
├── durationRange: ClosedRange<Int>?  // minutes
├── genres: Set<String>
├── mood: String?
├── energyProfile: EnergyCurveProfile?
└── keywords: Set<String>
```

### Modèles d'actions

| Modèle | Rôle |
|--------|------|
| `OpenPlaylistRequest` | Visualiser le contenu |
| `ModifyPlaylistRequest` | Préremplit le builder → nouvelle playlist |
| `VariationRequest` | Copie paramètres + contenu comme base → nouvelle playlist |
| `MergePlaylistsRequest` | Fusion N playlists → nouvelle entrée |
| `InspirationRequest` | Point d'entrée IA future (ambiance, énergie, style) |
| `PublishPlaylistRequest` | Publier vers un provider sans modifier le contenu |
| `ExportPlaylistRequest` | M3U / CSV / JSON (ADR-016) |
| `DeletePlaylistRequest` | Suppression avec confirmation |

---

## Actions utilisateur du Répertoire

| Action | Comportement |
|--------|--------------|
| ▶ **Ouvrir** | Afficher le contenu (`RepertoireDetailView`) |
| ✏ **Modifier** | Retour au workflow de génération avec paramètres préremplis ; génération → **nouvelle** playlist |
| 🎵 **Envoyer vers un provider** | Publication directe, aucune modification préalable |
| 📄 **Créer une variation** | Nouvelle playlist indépendante, paramètres préremplis, modifiables |
| 🔀 **Fusionner** | Fusion de plusieurs playlists du Répertoire |
| ✨ **Quelle source d'inspiration !** | Nouvelle playlist inspirée (ambiance, énergie, style ; autres artistes/titres) — entrée IA future |
| 🗑 **Supprimer** | Suppression avec confirmation |

---

## Ports applicatifs (futurs)

| Port | Responsabilité |
|------|----------------|
| `PlaylistRepositoryPort` | CRUD Répertoire, filtres, merge |
| `PlaylistPublicationPort` | Publier une `SavedPlaylist` vers un provider |
| `PlaylistExportPort` | M3U, CSV, JSON depuis `CanonicalPlaylist` |
| `PlaylistInspirationPort` | Génération inspirée (stub → IA) |

`ProviderImportPort` reste inchangé (ADR-012). La publication Répertoire l'utilise en interne sans le modifier.

### Commandes bridge prévues

| Commande | Description |
|----------|-------------|
| `list_repertoire` | Liste + filtres |
| `get_repertoire_playlist` | Détail complet |
| `save_to_repertoire` | Sauvegarde après génération |
| `delete_repertoire_playlist` | Suppression |
| `merge_repertoire_playlists` | Fusion |
| `publish_repertoire_playlist` | Stream événements (pattern import) |
| `export_repertoire_playlist` | Export fichier |
| `inspire_from_repertoire_playlist` | Stub IA |

Les commandes historique existantes (`list_history`, etc.) restent inchangées.

---

## ViewModels (conception)

| ViewModel | Responsabilités |
|-----------|-----------------|
| `RepertoireViewModel` | Liste, filtres, sélection, suppression, déclenchement des actions |
| `RepertoireDetailViewModel` | Détail, barre d'actions, publications passées |
| `PlaylistPublicationViewModel` | Choix provider, progression publication (VM dédié, pas `ImportViewModel`) |
| `PlaylistMergeViewModel` | Sélection multiple, stratégie, aperçu merge |

### Évolutions ViewModels existants

| ViewModel | Évolution |
|-----------|-----------|
| `PlaylistBuilderViewModel` | `BuilderEntryMode` : `.fresh`, `.modifyFrom`, `.variationFrom`, `.inspiredFrom` ; `loadFromSavedPlaylist()` |
| `ImportViewModel` | Inchangé pour Nouvelle Playlist → Import |
| `HistoryViewModel` | Rôle audit ; lien « Ouvrir dans le Répertoire » si `savedPlaylistID` présent |
| `AppWorkflowCoordinator` | `repertoire: RepertoireViewModel`, `pendingRepertoireIntent`, orchestration cross-écrans |

---

## Écrans (conception)

### Navigation

`SidebarItem` : ajouter `repertoire` entre `newPlaylist` et `history`.  
`AppRoute` : ajouter `repertoire`, `repertoireDetail`.

### Nouveaux écrans

| Écran | Description |
|-------|-------------|
| `RepertoireView` | Liste filtrable, recherche, actions groupées |
| `RepertoireDetailView` | Contenu, métadonnées, publications, barre d'actions |
| `PlaylistPublishView` | Choix provider, progression |
| `PlaylistMergeView` | Sélection N playlists, stratégie, aperçu |
| `PlaylistInspirationView` | Stub UI — point d'entrée IA |

### Écrans modifiés (futurs — hors Phase 6.0)

| Écran | Modification |
|-------|-------------|
| `HomeView` | Raccourci **Répertoire** |
| `PlaylistPreviewView` | « Sauvegarder dans le Répertoire » |
| `HistoryView` | Recentrage audit |

**Phase 6.0** : documentation et fondations uniquement ; l'UX actuelle (Phase 5.5) n'est pas modifiée tant que la stabilisation n'est pas mergée.

---

## Extensibilité multi-providers et exports

| Destination | Mécanisme | Impact `SavedPlaylist` |
|-------------|-----------|------------------------|
| Apple Music | `PlaylistPublicationPort` → gateway Apple | Aucun |
| Spotify / YouTube Music | Nouveaux gateways | Aucun |
| M3U / CSV / JSON | `PlaylistExportPort` | Aucun |

---

## Migration Historique → Répertoire

1. Introduire le Répertoire (vide).
2. Proposer « Sauvegarder dans le Répertoire » après génération réussie.
3. Script de migration optionnel : sessions `imported` / `partial_success` → `SavedPlaylist` (non destructif pour l'historique).
4. Déprécier progressivement « Modifier depuis l'Historique » au profit du Répertoire.

---

## Plan d'implémentation suggéré

| Phase | Contenu |
|-------|---------|
| **6.0 — Fondations** | Modèles, `PlaylistRepositoryPort`, persistance, `RepertoireView` (liste/ouvrir/supprimer), navigation |
| **6.1 — Actions création** | Modifier, Variation, auto-save, `BuilderEntryMode` |
| **6.2 — Publication** | `PlaylistPublicationPort`, publication Apple depuis Répertoire |
| **6.3 — Filtres & Fusion** | Filtres UI, `PlaylistMergeView` |
| **6.4 — Inspiration** | `PlaylistInspirationPort` stub, UI inspiration |
| **6.5 — Exports** | M3U / CSV / JSON |
| **6.6+ — Multi-provider** | Spotify, YouTube Music |

---

## Hors périmètre (Phase 6 docs)

- Aucune modification de `ProviderImportPort`
- Aucune modification du workflow d'acquisition manuelle (ADR-012)
- Aucune modification de l'UX Phase 5.5 en cours de stabilisation
- Aucun code runtime dans ce livrable documentaire

## Références

- [ADR-014](../architecture/ADR-014-repertoire-as-first-class-playlist-library.md)
- [ADR-015](../architecture/ADR-015-playlist-publication-as-provider-destination.md)
- [ADR-016](../architecture/ADR-016-playlist-export-formats.md)
- [ADR-017](../architecture/ADR-017-playlist-lineage-without-versioning.md)
- [ADR-013](../architecture/ADR-013-multi-provider-platform-vision.md)
- [phase-4-session-history.md](phase-4-session-history.md)
