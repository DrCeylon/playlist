# Phase 6 — Provider Platform & Real Sync

**Branche de conception :** `cursor/phase-provider-sync-real-gateways`  
**Base :** `main` @ `d33ce9a` (tag `phase-playlist-manager-complete`)  
**Statut :** Conception — aucune implémentation runtime dans cette étape

## Objectif

Faire évoluer Resonance d’un gestionnaire de playlists **local/stub** vers une plateforme **provider-neutral** capable de :

- lire des playlists distantes (compte provider ou source ouverte) ;
- persister des snapshots locaux manipulables ;
- synchroniser (dry-run puis apply) vers/depuis un provider ;
- comparer des versions multi-provider ;
- conserver le workflow **génération → import Apple Music** et **manual acquisition / retry** intacts.

## Principes non négociables

| Principe | Implication |
|----------|-------------|
| Core provider-neutral | `ResonanceCore` et `canonical/` n’importent aucun SDK Apple/YouTube/Spotify |
| Playlist Resonance = vérité locale | Les providers sont sources ou destinations, jamais propriétaires du modèle métier |
| `ProviderImportPort` gelé | Pas de modification sans ADR dédiée ; sync ≠ import streaming |
| Apple Music stable | Premier gateway read/write « production » |
| YouTube expérimental | `ProviderCapability.experimental` + gateway isolé |
| Spotify extensible | Registry + ports sans changement de modèle métier |
| Sources ouvertes | JSON / CSV / URL publique = `PlaylistSourceKind.publicCatalog` |

---

## 1. Diagnostic architectural

### 1.1 Déjà prêt pour le multi-provider réel

| Zone | Élément | Détail |
|------|---------|--------|
| **Python canonical** | `ProviderGateway`, `CatalogSearchPort`, `LibraryResolvePort`, `PlaylistDeliveryPort` | `canonical/contracts.py` |
| **Python runtime** | `ProviderGatewayRegistry`, `IntegrationGateway` | Enregistrement Apple Music opérationnel |
| **Python import** | `ProviderImportPort` | Streaming import + manual acquisition (ADR-012) |
| **Python enums** | `ProviderId`, `ProviderCapability` | Inclut `PLAYLIST_LIBRARY_BROWSE`, `PLAYLIST_SYNC`, `EXPERIMENTAL` |
| **Swift Core** | `ProviderID`, `ProviderCapability`, `ProviderOption` | Miroir bridge |
| **Swift Core** | `PlaylistLibraryModels` | Statuts sync, conflits, directions, source kinds |
| **Bridge** | `list_managed_playlists`, `get_managed_playlist`, `sync_managed_playlist` | Contrats JSON stables |
| **UI** | `PlaylistsView`, `SyncView`, `ProvidersView` | Navigation et VM découplés via protocoles |
| **Vision** | ADR-013 | Positionnement multi-provider documenté |

### 1.2 Encore stub / mock

| Zone | Élément | Limite actuelle |
|------|---------|-----------------|
| **Python** | `playlist_library.py` | Playlists dérivées de **l’historique** uniquement ; tracks vides |
| **Python** | `sync_managed_playlist_stub` | Retourne toujours `pending` |
| **Swift** | `DefaultManagedPlaylists.samples` | Fallback hors bridge |
| **Swift** | `MockPlaylistLibraryService` | Sync simulée |
| **Swift** | `ProvidersViewModel` | Lit diagnostics, pas d’auth réelle |
| **Swift** | `PlaylistBuilderViewModel` | `providerID` hardcodé `.appleMusic` |
| **Python** | Aucun `ProviderPlaylistReadPort` | Pas de list/get playlist distante |
| **Persistance** | Pas de `LocalPlaylistRepository` | Pas de store dédié hors session history |

### 1.3 Doit devenir un port applicatif

| Port proposé | Responsabilité |
|--------------|----------------|
| `ProviderPlaylistReadPort` | Lister / lire playlists et tracks distants |
| `ProviderPlaylistWritePort` | Créer / mettre à jour / publier playlist distante |
| `ProviderAuthPort` | État connexion, configuration compte (par provider) |
| `LocalPlaylistRepository` | CRUD snapshots locaux Resonance |
| `PlaylistSyncEngine` | Orchestration plan → dry-run → apply |
| `PlaylistConflictResolver` | Résolution ou escalade conflits |
| `PlaylistComparisonService` | Diff local / remote / cross-provider |

### 1.4 Doit rester provider-neutral

- DTO Swift `ResonanceCore` (Managed*, Remote*, Sync*, Comparison*)
- `PlaylistLibraryServing` / futurs protocoles VM
- `PlaylistSyncEngine` (Python application layer)
- Bridge commands & `BridgePayloadBuilder`
- ViewModels et Screens (labels via `ProviderID` + capabilities, pas AppleScript)

### 1.5 Ne surtout pas coupler

| Interdit dans Core / UI générique | Autorisé dans gateway provider |
|-----------------------------------|-------------------------------|
| `persistent_id`, AppleScript | `integration/apple_music/` |
| OAuth headers YouTube | `integration/youtube_music/` (expérimental) |
| URI Spotify | `integration/spotify/` (futur) |
| Logique sync dans `import_stream.py` | Nouveau module `playlist_sync/` |

---

## 2. Architecture Provider Platform

### 2.1 Vue en couches

```text
┌─────────────────────────────────────────────────────────────┐
│ ResonanceMac (SwiftUI)                                       │
│ PlaylistsVM / SyncVM / ProvidersVM — protocoles uniquement   │
└───────────────────────────┬─────────────────────────────────┘
                            │ bridge JSON
┌───────────────────────────▼─────────────────────────────────┐
│ Bridge runtime (json_rpc)                                      │
│ list_remote_playlists, import_remote_playlist,               │
│ plan_sync, apply_sync, compare_playlists, provider_auth_*     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ Application (use cases)                                      │
│ PlaylistSyncEngine, PlaylistComparisonService,               │
│ ImportRemotePlaylist, PublishLocalPlaylist                   │
└───────┬───────────────────────────────┬───────────────────┘
        │                               │
┌───────▼────────┐            ┌─────────▼──────────────────┐
│ LocalPlaylist  │            │ ProviderGatewayRegistry     │
│ Repository     │            │ + IntegrationGateway        │
└────────────────┘            └─────────┬──────────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
     ┌────────▼────────┐     ┌─────────▼────────┐    ┌──────────▼──────────┐
     │ AppleMusic       │     │ YouTubeMusic      │    │ Spotify (future)    │
     │ ProviderGateway  │     │ ExperimentalGw    │    │ stub                │
     │ + Read/Write     │     │ + Read (limited)  │    │                     │
     │   ports          │     │                   │    │                     │
     └──────────────────┘     └───────────────────┘    └─────────────────────┘
```

### 2.2 Composants

| Composant | Couche | Rôle |
|-----------|--------|------|
| **ProviderRegistry** | Existant (`ProviderGatewayRegistry`) | Résolution `ProviderId` → gateway |
| **ProviderGateway** | Existant (étendu) | Façade capabilities + ports |
| **ProviderPlaylistReadPort** | Nouveau port | `list_playlists`, `get_playlist`, `get_tracks` |
| **ProviderPlaylistWritePort** | Nouveau port | `create_playlist`, `upsert_tracks`, `delete_tracks` |
| **ProviderAuthPort** | Nouveau port | `auth_state`, `connect`, `disconnect` |
| **RemotePlaylistSnapshot** | DTO | Image immuable d’une playlist distante à un instant T |
| **LocalPlaylistRepository** | Infra/app | Persistance fichiers SQLite ou JSON store |
| **PlaylistSyncEngine** | Application | Build plan, dry-run, apply, journalise opérations |
| **PlaylistConflictResolver** | Domain | Règles par `SyncMode` |
| **PlaylistComparisonService** | Application | Diff tracks/metadata entre deux snapshots |

### 2.3 Relation avec `ProviderImportPort`

```
Génération → import_stream → ProviderImportPort     (INCHANGÉ — ADR-012)
Bibliothèque → PlaylistSyncEngine → Read/Write ports (NOUVEAU — ADR-016)
```

Un **publish** vers Apple Music réutilise la **delivery** existante pour l’ajout de morceaux, mais passe par `PlaylistSyncEngine` — pas par un second chemin ad hoc dans `import_stream`.

---

## 3. Modèles métier proposés

### 3.1 Tableau synthétique

| Modèle | Couche | Persisté | Bridge JSON |
|--------|--------|----------|-------------|
| `RemotePlaylist` | Core DTO | Non (transient) | `remote_playlist` |
| `RemotePlaylistTrack` | Core DTO | Non | dans `remote_playlist.tracks` |
| `RemoteProviderAccount` | Core DTO | Oui (secrets hors repo) | `provider_account` |
| `LocalManagedPlaylist` | Core + Repository | Oui | `managed_playlist` (évolution de `ManagedPlaylistSummary`) |
| `PlaylistSyncPlan` | Application | Non (session) | `sync_plan` |
| `PlaylistSyncOperation` | Application | Oui (journal) | `sync_operation` |
| `PlaylistSyncConflict` | Existant (enrichi) | Dans opération | `sync_conflicts` |
| `PlaylistComparisonResult` | Application | Non | `comparison` |
| `ProviderAuthState` | Core DTO | Dérivé | `auth_state` |
| `SyncDirection` | Existant | — | `direction` |
| `SyncMode` | Nouveau enum | — | `sync_mode` |

### 3.2 Détail des modèles

#### `RemotePlaylist`
- **Couche :** `ResonanceCore` + `playlist_builder/ui/shared/dto/`
- **Champs :** `providerID`, `remotePlaylistID`, `name`, `trackCount`, `isPublic`, `ownerLabel`, `snapshotAtISO`, `sourceURL`
- **Invariants :** `remotePlaylistID` opaque, unique par `(providerID, remotePlaylistID)`
- **Persisté :** non — obtenu via ReadPort

#### `RemotePlaylistTrack`
- **Champs :** `remoteTrackID`, `artist`, `title`, `album`, `durationMS`, `position`, `providerMetadata` (dict neutre)
- **Invariants :** pas de PID Apple en clair dans le DTO bridge partagé ; mapping dans gateway

#### `RemoteProviderAccount`
- **Champs :** `providerID`, `displayName`, `authState`, `lastConnectedAtISO`, `capabilities`
- **Invariants :** tokens stockés côté Keychain (macOS) ou fichier chiffré local — jamais dans le bridge log
- **Persisté :** métadonnées oui, secrets non (Keychain)

#### `LocalManagedPlaylist`
- **Évolution de** `ManagedPlaylistSummary`
- **Champs ajoutés :** `canonicalPlaylistID`, `linkedRemoteRefs[]`, `lastSyncOperationID`, `syncMode`, `localRevision`
- **Invariants :** une playlist Resonance a un `localPlaylistID` stable ; zéro ou plusieurs liens provider
- **Persisté :** oui (`LocalPlaylistRepository`)

#### `PlaylistSyncPlan`
- **Champs :** `localPlaylistID`, `targetProviderID`, `direction`, `syncMode`, `actions[]` (add/remove/reorder/map)
- **Invariants :** produit par dry-run ; immuable une fois calculé
- **Persisté :** non (cache session optionnel)

#### `PlaylistSyncOperation`
- **Champs :** `operationID`, `plan`, `status`, `startedAt`, `finishedAt`, `appliedActions`, `conflicts`
- **Persisté :** oui (audit + UI historique sync)

#### `PlaylistComparisonResult`
- **Champs :** `leftSnapshotRef`, `rightSnapshotRef`, `matched`, `onlyLeft`, `onlyRight`, `metadataMismatches`
- **Invariants :** compare par clé canonique `(artist, title, normalized)` + mapping provider quand dispo

#### `ProviderAuthState` (enum)
- `disconnected`, `configured`, `connected`, `expired`, `error`, `experimental_unavailable`

#### `ProviderCapability` (extensions proposées)
- Existants suffisants pour v1 ; optionnel futur : `playlist_publish`, `oauth_connect`

#### `SyncDirection` (existant)
- `pullFromProvider`, `pushToProvider`, `bidirectionalPreview`

#### `SyncMode` (nouveau)
- `mirror` — aligner destination sur source
- `append_only` — ajouter sans supprimer
- `dry_run` — plan sans apply
- `manual_resolve` — stop sur conflit

---

## 4. Flux UX cibles

### A. Connecter un provider

1. **Providers** → carte YouTube (badge Expérimental) ou Apple Music  
2. Action **Connecter** → sheet configuration (OAuth / Music.app déjà actif pour Apple)  
3. VM appelle `provider_auth_status` / `provider_connect`  
4. Retour : `ProviderAuthState.connected` → `isConnected=true` dans `ProviderOption`

### B. Importer une playlist distante

1. **Synchronisation** → choisir provider connecté  
2. Liste `RemotePlaylist` via `list_remote_playlists`  
3. Sélection → **Importer localement**  
4. Crée `LocalManagedPlaylist` + snapshot tracks + option variation (nom dérivé)  
5. Redirection **Playlists** avec détail hydraté

### C. Synchroniser locale → provider

1. **Playlists** → playlist locale → **Publier / Sync**  
2. Choisir provider cible (pré-rempli si lien existant)  
3. **Dry-run** affiche `PlaylistSyncPlan` (ajouts/suppressions)  
4. Confirmer → `apply_sync` → statut `synced` / `partial` / `conflict`

### D. Comparer deux providers

1. Playlist locale avec liens Apple + YouTube  
2. Action **Comparer** → `compare_playlists`  
3. Écran diff : matched / only Apple / only YouTube / metadata mismatch  
4. Pas d’écriture automatique en v1

### E. Créer une variation depuis distante

1. Import YouTube → **Créer variation**  
2. Clone `LocalManagedPlaylist` avec nouveau `localPlaylistID`, `sourceKind=providerLibrary`, pas de lien write tant que non publié  
3. Édition future (hors scope v1) sur la copie locale

---

## 5. Stratégie YouTube Music

### Options réalistes

| Option | Fiabilité | Auth | Recommandation |
|--------|-----------|------|----------------|
| **ytmusicapi** (non officiel) | Moyenne — cassable | Cookies OAuth navigateur | Gateway expérimental isolé, opt-in |
| **Export JSON/CSV** | Haute | Aucune | Fallback v1 — import manuel fichier |
| **URL playlist publique** | Variable | Aucune | Lecture limitée si API instable |
| **API officielle** | N/A | Pas d’API playlist consumer publique | Non viable aujourd’hui |

### Recommandation prudente (ADR-018)

1. **Ne pas** ajouter `ytmusicapi` aux dépendances runtime par défaut.  
2. Module optionnel `playlist_builder/integration/youtube_music/` derrière extra `[youtube]`.  
3. UI : badge **Expérimental**, disclaimer ToS, échec gracieux → proposer import fichier.  
4. Capabilities : `catalog_search` + `experimental` uniquement jusqu’à validation.  
5. Pas de write YouTube en v1 — read + import local seulement.  
6. Comparaison Apple/YouTube via snapshots locaux, pas live cross-API.

---

## 6. Plan d’implémentation par sous-phases

### 6.1 Provider Platform Contracts

| | |
|--|--|
| **Fichiers** | `integration/ports/playlist_read.py`, `playlist_write.py`, `provider_auth.py` ; DTO Swift/Python ; ADR-014 |
| **Tests** | Contract tests ports + registry capability gating |
| **Risques** | Sur-ingénierie — garder ports minimaux |
| **Rollback** | Ports sans implémentation |
| **Validation** | `pytest` ports ; `swift test` DTO decode |

### 6.2 Remote Playlist Read

| | |
|--|--|
| **Fichiers** | Apple read adapter ; bridge `list_remote_playlists`, `get_remote_playlist` |
| **Tests** | Mock gateway ; bridge round-trip |
| **Risques** | Apple Music library API limitée — scope « playlists utilisateur Music.app » |
| **Rollback** | Feature flag bridge command |
| **Validation** | Liste non vide sur compte test macOS |

### 6.3 Local Import from Provider

| | |
|--|--|
| **Fichiers** | `LocalPlaylistRepository` ; `ImportRemotePlaylist` use case ; hydrate tracks |
| **Tests** | Repository CRUD ; import crée `LocalManagedPlaylist` |
| **Risques** | Duplication avec session history — lier via `historySessionID` optionnel |
| **Rollback** | Repository derrière interface |
| **Validation** | Import visible dans Playlists UI |

### 6.4 Sync Plan / Dry Run

| | |
|--|--|
| **Fichiers** | `PlaylistSyncEngine` ; `plan_sync` bridge ; ADR-016 |
| **Tests** | Plan sur fixtures ; dry-run sans side effects |
| **Risques** | Complexité diff — commencer append_only |
| **Rollback** | Stub plan détaillé |
| **Validation** | UI affiche actions proposées |

### 6.5 Apple Music publish/read alignment

| | |
|--|--|
| **Fichiers** | `AppleMusicPlaylistReadPort`, write via delivery existante |
| **Tests** | Non-régression `test_provider_import_port`, manual acquisition, retry |
| **Risques** | Régression import — suite CI obligatoire |
| **Rollback** | Désactiver write port |
| **Validation** | Push playlist test + import génération inchangé |

### 6.6 YouTube Music experimental gateway

| | |
|--|--|
| **Fichiers** | `integration/youtube_music/` ; ADR-018 ; optional deps |
| **Tests** | Mock + skip intégration sans credentials |
| **Risques** | API breakage, légal |
| **Rollback** | Désinstaller extra ; gateway non enregistré |
| **Validation** | Import fichier JSON + liste vide gracieuse sans auth |

### 6.7 Conflict resolution

| | |
|--|--|
| **Fichiers** | `PlaylistConflictResolver` ; enrichir `PlaylistSyncConflict` |
| **Tests** | Cas duplicate, missing, metadata mismatch |
| **Risques** | UX complexe — manual_resolve par défaut |
| **Rollback** | Stop at first conflict |
| **Validation** | Conflits visibles Sync UI |

### 6.8 UX polish

| | |
|--|--|
| **Fichiers** | Providers connect flow ; Sync wizard ; Compare view |
| **Tests** | VM tests ; navigation guards |
| **Risques** | Scope creep |
| **Rollback** | Feature flags par écran |
| **Validation** | Parcours manuel macOS |

---

## 7. ADR

| ADR | Titre | Fichier |
|-----|-------|---------|
| ADR-014 | Provider Gateway Architecture (playlist read/write) | `docs/architecture/ADR-014-provider-gateway-architecture.md` |
| ADR-015 | Provider Authentication Boundary | `docs/architecture/ADR-015-provider-auth-boundary.md` |
| ADR-016 | Playlist Sync Model | `docs/architecture/ADR-016-playlist-sync-model.md` |
| ADR-017 | Remote Playlist Snapshot | `docs/architecture/ADR-017-remote-playlist-snapshot.md` |
| ADR-018 | Experimental YouTube Music Gateway | `docs/architecture/ADR-018-experimental-youtube-music-gateway.md` |

> **Note numérotation :** La wiki Phase 5.4 proposait d’autres sujets pour ADR-014–017. La phase 6 **réassigne** ces numéros aux contrats ci-dessus. Les sujets Spotify-specific restent des sous-sections d’ADR-014.

---

## 8. Tests à prévoir

### Python

| Domaine | Tests |
|---------|-------|
| DTO bridge | `test_remote_playlist_dto.py`, extension `test_playlist_library_bridge.py` |
| ProviderCapability | Gating registry : read sans capability → erreur |
| ProviderRegistry | Gateway stub enregistré / requis |
| PlaylistSyncPlan | Dry-run fixtures |
| ConflictResolver | Matrices de conflits |
| Remote import | Mock ReadPort → LocalRepository |
| Non-régression | `test_provider_import_port`, `test_manual_acquisition_*`, `test_retry_import_*`, `test_import_stream_checkpoint_resume` |

### Swift

| Domaine | Tests |
|---------|-------|
| Bridge decode | `RemotePlaylist`, `PlaylistSyncPlan`, `ProviderAuthState` |
| PlaylistsVM | Import, sync dry-run feedback |
| ProvidersVM | Auth state display |
| Guards | `ProviderNeutralGuardTests` inchangé |
| Non-régression | `ImportViewModelTests` (retry, manual, late events) |

---

## 9. Risques

| Risque | Mitigation |
|--------|------------|
| Régression import Apple | Suite non-régression dédiée ; pas de touch `ProviderImportPort` |
| Couplage Apple dans Core | Guards + revue ports |
| YouTube instable | Experimental + fallback fichier |
| Double source de vérité (history vs repository) | `LocalManagedPlaylist` canonical ; history = audit génération |
| Scope explosion | Sous-phases 6.1–6.8 strictes |

---

## 10. Prochaine étape recommandée

**Sous-phase 6.1 uniquement :** introduire les ports Python + DTO bridge + tests contractuels, sans UI ni gateway réel.

Commit de conception sur `cursor/phase-provider-sync-real-gateways` → revue → merge docs → démarrer 6.1.

## Références

- ADR-013 Multi-provider platform vision
- ADR-012 Apple acquisition production policy
- `docs/TECHNICAL_DEBT.md`
- `wiki/Phase-Playlist-Manager-Cloture.md`
