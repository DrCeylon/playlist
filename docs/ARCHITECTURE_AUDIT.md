# Audit d'architecture — Resonance v1.0 (juillet 2026)

**Rôle :** Principal Engineer — audit préparatoire aux cinq prochaines années.  
**Périmètre :** `playlist_builder/` (~219 fichiers Python), shell Swift `apps/resonance/`, documentation ADR.  
**Méthode :** analyse statique des imports, lecture des ADR, revue des tests d'architecture, parcours des chemins critiques (bridge → sync → repository → providers).  
**Aucune fonctionnalité ajoutée** — uniquement diagnostic et correctifs à ROI démontré.

Documents liés : [ADR-022](architecture/ADR-022-layering-and-future-readiness.md) · [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) · [TARGET_ARCHITECTURE.md](architecture/TARGET_ARCHITECTURE.md)

---

## 1. Résumé exécutif

Resonance v1.0 est un **monolithe modulaire bien structuré** autour de trois piliers solides :

1. **Moteur de sync provider-neutral** (`app/playlist_sync/`) avec garde-fous AST empêchant les imports provider.
2. **Plateforme multi-provider** (`integration/gateway/`, ports, registry) alignée ADR-013/014.
3. **Persistance locale verrouillée** (`infrastructure/atomic_json.py`) pour le SSOT JSON.

Le **défaut structurel dominant** est l'inversion de dépendance : les agrégats domaine (playlists gérées, snapshots, plans sync) vivent sous `ui/shared/dto/` et sont importés par `integration/ports/`, `app/playlist_sync/` et la persistance. Cela contredit la règle « dépendances vers l'intérieur » et amplifiera le coût de SQLite, cloud sync, plugins et API publique.

**Verdict :** architecture **production-ready pour v1.0 local-first**, avec une dette de **couche domaine** à traiter avant Resonance 2.0.

### Correctifs implémentés (ROI démontré)

| Correctif | Problème réel aujourd'hui | Fichiers |
|-----------|---------------------------|----------|
| Échec explicite sur schema_version trop récent | Effacement silencieux des playlists | `json_repository.py`, `errors.py` |
| `get_playlist` sans tri inutile | O(n log n) par lookup | `json_repository.py` |
| Verrouillage snapshots | Course inter-processus possible | `snapshot_archive.py` |
| Import manquant `ProviderPlaylistWritePort` | Analyse statique / IDE cassés | `action_executor.py` |
| Guards architecture couche | Régression des frontières | `tests/test_layer_architecture.py` |

---

## 2. Architecture globale

### 2.1 Vue d'ensemble

```text
┌─────────────────────────────────────────────────────────────┐
│ Surfaces : SwiftUI macOS · CLI · engine_bridge (JSON-RPC)    │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│ ui/bridge + ui/shared (DTO, history, theme)                  │
│   └─ JsonRpcEngineBridge → RuntimeEngineBridgeBackend (547L) │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│ app/ — use cases, bridge_runtime, playlist_library, sync     │
└──────────┬─────────────────────────────┬────────────────────┘
           │                             │
┌──────────▼──────────┐    ┌─────────────▼────────────────────┐
│ canonical/          │    │ integration/ (gateways, ports)   │
│ modèle composition  │    │ apple_music · youtube_music        │
└─────────────────────┘    └──────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────┐
│ infrastructure/ · observability/ · platform/ · catalog/      │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 Ce qui fonctionne bien

| Force | Preuve |
|-------|--------|
| Sync plan/apply séparés | ADR-016, checksums, idempotence, `test_sync_architecture.py` |
| Ports d'import canoniques | `ProviderImportPort` utilise `canonical.models` |
| Registry extensible | `ProviderGatewayRegistry` + `ExtensionPointId.MUSIC_PROVIDER` |
| Persistance atomique | `locked_json_document` + RMW sur `managed_playlists.json` |
| Traçabilité ADR | 21 ADR + TARGET_ARCHITECTURE + vision 2030 |
| Tests d'architecture | Sync provider-blind, conflits sans import provider |

### 2.3 Risque structurel #1 — DTO domaine sous `ui/`

**34 fichiers** dans `app/` et **10** dans `integration/` importent `ui.shared.dto`.

Les types SSOT (`ManagedPlaylistDetail`, `RemotePlaylistSnapshot`, `PlaylistSyncPlan`) sont des **agrégats domaine**, pas des view models. Leur emplacement sous `ui/` force :

- `integration/ports/playlist_read.py` → import UI (violation layering)
- Plugins futurs dépendant du package UI pour les contrats port
- Migration SQLite liée au schéma `to_dict()` des DTO UI
- Swift et Python couplés au même namespace « ui »

**Recommandation (non implémentée — effort élevé) :** extraire `playlist_builder/domain/` (ou promouvoir types vers `app/domain/`), garder des mappers fins dans `ui/shared/dto` pour le bridge Swift.

---

## 3. Analyse par couche

### 3.1 Frontières entre modules

| Frontière | État | Problème |
|-----------|------|----------|
| `canonical/` ↔ `core/` | Coexistence | `core/models.PlaylistDefinition` encore utilisé par bridge import ; `canonical/compat.py` shim lazy |
| `app/playlist_sync/` ↔ `integration/` | Bon (planning) | `action_executor` / `apply` référencent `ProviderPlaylistWritePort` — acceptable pour couche apply |
| `integration/ports/` ↔ `ui/` | **Inversé** | Ports dépendent de DTO UI |
| `observability/` ↔ `app/` | **Inversé** | `health.py` importe `AppContext` |
| `catalog/` ↔ `integration/apple_music/` | Chevauchement | Deux surfaces recherche Apple (legacy vs gateway) |
| History ↔ Repository | Transition | `HistoryToRepositoryMigration` — double persistance temporaire |

### 3.2 Découpage des packages

| Package | Responsabilité réelle | Ambiguïté |
|---------|----------------------|-----------|
| `ui/shared/dto/` | Domaine + bridge | Nom et emplacement trompeurs |
| `ui/shared/history/` | Sessions génération/import | Chez UI mais consommé par app |
| `app/bridge_runtime/` | Facades + god object backend | 30 commandes, 547 lignes |
| `platform/` | Manifest + extension points | Pas de loader dynamique |
| `planning/` vs `session/` | Deux pipelines génération | Legacy parallèle |
| `music/` vs `integration/apple_music/` | Client Music.app legacy | Triple stack import |

### 3.3 Bridge (`ui/bridge` + `app/bridge_runtime`)

**Flux :** Swift → stdin JSON → `cli/engine_bridge.py` → `JsonRpcEngineBridge` → `RuntimeEngineBridgeBackend` → stdout JSON-lines.

| Problème | Impact 2–3 ans | Sévérité |
|----------|----------------|----------|
| Process one-shot par commande | Latence imports longs, pas de session chaude | Moyen |
| `backend.py` god object (30+ méthodes) | Chaque nouvelle commande augmente le risque régression | Moyen |
| `EngineBridgeBackend` Protocol incomplet | Sync/history/auth hors contrat formel | Faible |
| `sync_managed_playlist` stub | API confuse pour consommateurs | Faible |
| Defaults `ProviderId.APPLE_MUSIC` hardcodés | Multi-provider incomplet côté acquisition | Moyen |
| Double modèle playlist au bridge | `PlaylistDefinition` legacy + DTO génération | Moyen |

### 3.4 Repository

| Composant | Stockage | Limite v1.0 |
|-----------|----------|-------------|
| `JsonManagedPlaylistRepository` | `managed_playlists.json` RMW | Document entier réécrit à chaque upsert |
| `SnapshotArchive` | `snapshots/{checksum}.json` immuable | Pas d'index temporel |
| `JsonPlaylistSyncOperationRepository` | `sync_operations.json` | Append/update, pas de pagination |

**Problèmes corrigés :**
- Schema version trop récent → **erreur explicite** (plus d'effacement silencieux)
- `get_playlist` → lookup sans tri superflu
- Snapshots → **verrou `fcntl`** aligné sur managed playlists

**Problèmes restants :**
- O(n) scan linéaire — acceptable jusqu'à ~500 playlists / 5k tracks, critique au-delà
- Pas d'émission `REPOSITORY_UPSERT` / `SNAPSHOT_STORED` malgré kinds définis
- Sérialisation couplée à `ui.shared.dto.to_dict()`

### 3.5 Sync engine

| Composant | Rôle | État |
|-----------|------|------|
| `PlaylistSyncEngine` | Plan only, provider-blind | ✅ Solide |
| `PlaylistConflictDetector` | 7 types de conflits | ✅ |
| `PlaylistConflictResolver` | Résolution utilisateur | ✅ |
| `SyncActionExecutor` | Exécution push/pull | **Partiel** |
| `ApplySyncPlaylist` | Validation + idempotence | ✅ |

**Écart plan ↔ apply (problème réel documenté KNOWN_LIMITATIONS) :**

| Action planifiée | Push apply | Pull apply |
|------------------|------------|------------|
| `add_track` | ✅ | ✅ |
| `remove_track` | ✅ | ❌ |
| `reorder` | skipped « 6.5 » | skipped |
| `rename_playlist` | skipped | — |
| `map_track` | skipped | — |

**Risque :** l'utilisateur voit un plan avec des actions que l'apply ne peut pas exécuter → perte de confiance.  
**Recommandation :** filtrer au plan selon `ProviderCapability` ou documenter strictement les modes supportés (déjà partiellement dans KNOWN_LIMITATIONS).

**Hook mort :** `_append_duplicate_conflicts` est un no-op dans `planner.py`.

### 3.6 Provider platform

| Élément | État |
|---------|------|
| `ProviderGatewayRegistry` | 2 gateways enregistrés dans `factory.py` (pas de chargement dynamique) |
| `ProviderImportPort` | Contrat propre (canonical) ✅ |
| `ProviderPlaylistReadPort` / `WritePort` | Types UI DTO ❌ |
| `IntegrationGateway.import_playlist` | Duck-typing `getattr(gateway, "import_service")` |
| YouTube | Lecture/expérimental, pas de write fiable |

**Triple stack import :** CLI direct, bridge `import_stream`, gateway `import_service` — trois chemins de câblage Apple.

### 3.7 Observability

| Élément | État |
|---------|------|
| Bus in-process | 2000 events max, singleton global |
| Sync events | plan/apply émis ✅ |
| Import/generation events | kinds définis, émission partielle |
| `health.py` | Dépend de `AppContext` + `ProviderOption` UI |
| Diagnostics bridge | Union observability + plugins + history ✅ |

### 3.8 Plugin platform

| Existant | Manquant |
|----------|----------|
| `ExtensionPointId` (6 points, 3 actifs) | Loader dynamique |
| `parse_extension_manifest()` | Exécution entry points |
| Registry lié à extension point | Permissions / sandbox |
| Diagnostics `extension_points` | Bridge commands extensibles |

**Risque plugin :** un plugin externe devrait importer `ui.shared.dto` pour implémenter un port — inverse de l'isolation visée ADR-020.

### 3.9 UX (Swift)

| Limite | Impact futur |
|--------|--------------|
| `ProviderID` enum fermé Swift | Nouveau provider = changement Swift + Python |
| Bridge one-shot | UX import longue dégradée |
| Provider picker génération non branché | Multi-provider UI incomplet |
| Thème `fatalError` on load failure | Fragilité dev |

### 3.10 Performances

| Zone | Goulot | Seuil estimé |
|------|--------|--------------|
| JSON RMW repository | Réécriture document entier | >500 playlists |
| `list_playlists` | Parse + sort complet | >1000 playlists |
| Bridge cold start | Rebuild context | Imports >100 tracks |
| Identity cache | Fichier JSON | >50k entrées |
| Bus observability | Deque 2000 | Sessions longues |

### 3.11 Dette technique (synthèse)

Voir [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md). Priorités pour les 2–3 prochaines années :

1. **P0 structurel :** extraire domaine hors `ui/shared/dto`
2. **P1 fiabilité sync :** aligner plan et apply (ou filtrer au plan)
3. **P1 bridge :** facades + process persistant
4. **P2 scale :** backend SQLite derrière `ManagedPlaylistRepository` Protocol
5. **P2 import :** orchestrateur unique `ProviderImportPort`
6. **P3 plugins :** loader + contrats domaine stables

---

## 4. Couplages, abstractions, responsabilités

### 4.1 Couplages inutiles

| Couplage | Pourquoi inutile |
|----------|------------------|
| `integration/ports` → `ui.shared.dto` | Ports devraient dépendre du domaine |
| `observability/health` → `AppContext` | Health devrait accepter un registry seul |
| `app/factory` → `ui.bridge.errors.BridgeError` | Erreurs domaine ≠ erreurs bridge |
| `ui/bridge/json_rpc` → `core.models.PlaylistDefinition` | Legacy au lieu de canonical |

### 4.2 Abstractions inutiles

| Abstraction | Verdict |
|-------------|---------|
| `planning/` vs `session/` | Doublon partiel — consolider à terme |
| `sync_managed_playlist` stub | API morte — déprécier ou implémenter |
| `_append_duplicate_conflicts` no-op | Code mort — implémenter ou supprimer |
| `IntegrationGateway` duck-type import | Masque l'absence de port formel sur `ProviderGateway` |

### 4.3 Abstractions manquantes

| Manquante | Besoin |
|-----------|--------|
| Package `domain/` | SSOT types provider-neutral |
| `ImportOrchestrator` unique | Éliminer triple stack |
| `SupportedSyncCapabilities` au plan | Éviter plans non exécutables |
| `RepositoryEventEmitter` | Brancher observability repository |
| `PluginLoader` | ADR-020 phase 2 |
| `LocalHttpApi` (localhost) | TARGET_ARCHITECTURE 2.0 |

### 4.4 Responsabilités ambiguës

| Zone | Question ouverte |
|------|------------------|
| Qui possède le SSOT playlist ? | `ManagedPlaylistDetail` — oui, mais namespace UI |
| History vs Repository | Migration en cours — quand supprimer history ? |
| Catalog vs gateway search | Quelle surface pour la génération ? |
| Observability vs stderr logs | Quelle source de vérité diagnostic ? |

---

## 5. Scénarios futurs (2–5 ans)

### 5.1 Passage SQLite

| Prérequis | État actuel |
|-----------|-------------|
| `ManagedPlaylistRepository` Protocol | ✅ Existe |
| Sérialisation découplée UI | ❌ `serialization.py` → UI DTO |
| Migrations schema_version | ✅ Commencé (v1), rejet explicite si trop récent |
| Index par `local_playlist_id` | ❌ Scan linéaire |

**Chemin naturel :** `SqliteManagedPlaylistRepository` implémentant le Protocol existant, après extraction domaine. Pas de big-bang.

### 5.2 Synchronisation cloud (Resonance Services)

| Facteur | Préparation actuelle |
|---------|---------------------|
| `playlist_version` + checksum | ✅ Optimistic concurrency locale |
| Vector clocks / CRDT | ❌ |
| Séparation Music Providers / Resonance Services | ✅ ADR-013, ADR-019 |
| Audit log unifié | ❌ History + sync_operations séparés |
| Chiffrement / tenant | ❌ |

**Risque :** cloud sync sur JSON monolithique = conflits difficiles. SQLite + mutation log (`TARGET_ARCHITECTURE` `app/undo/`) préparent mieux.

### 5.3 API publique

| Surface | Maturité |
|---------|----------|
| Bridge JSON-RPC | 27 commandes, stable pour Swift |
| HTTP localhost | Non existant (TARGET_ARCHITECTURE) |
| Versioning API | `observability/api_version`, `platform/api_version` |
| Auth API | N/A local-first |

**Recommandation :** HTTP API = façade sur use cases existants, pas sur `backend.py` directement.

### 5.4 Versioning des données

| Entité | Versioning |
|--------|------------|
| `managed_playlists.json` | `schema_version=1`, rejet si > supported |
| `ManagedPlaylistDetail` | `playlist_version` par playlist |
| Snapshots | Immuables, checksum |
| Sync operations | `plan_checksum`, idempotency key |
| History sessions | Schema version séparé |

### 5.5 Multi-utilisateur

**Non préparé.** Chemins fichiers globaux, `fcntl` advisory locks process-local, pas de tenant_id. Acceptable v1.0 local-first. Toute évolution multi-user nécessite couche auth + isolation données dès la conception SQLite.

### 5.6 Très grosses bibliothèques

| Seuil | Comportement attendu | Aujourd'hui |
|-------|---------------------|-------------|
| 10k+ tracks / playlist | Pagination, index | Charge JSON entier |
| 1000+ playlists | Index, recherche | Scan + sort |
| Import 500+ tracks | Streaming, checkpoint | Checkpoint ✅, bridge one-shot ❌ |

### 5.7 Synchronisations simultanées

| Mécanisme | État |
|-----------|------|
| `fcntl` sur managed JSON | ✅ |
| Verrou snapshots | ✅ (corrigé cet audit) |
| Idempotence sync apply | ✅ |
| Sync parallèle 2 playlists | Possible (fichiers séparés) |
| Sync même playlist 2 processus | Protégé par version + checksum stale detection |

### 5.8 Providers distants multiples

| Capacité | État |
|----------|------|
| `LinkedRemoteRef` (N refs) | Modèle prêt |
| Orchestrateur multi-cible | Non implémenté |
| Sync simultanée Apple + YouTube | Non testé E2E |
| Capabilities par provider | ✅ `ProviderCapability` |

---

## 6. Matrice risque × horizon

| Risque | 1 an | 2–3 ans | 5 ans |
|--------|------|---------|-------|
| DTO sous UI | Gêne plugins | Bloque SQLite/API | Réécriture |
| Plan/apply gap sync | Frustration utilisateur | Perte confiance | Support coûteux |
| JSON scale | OK <500 playlists | Lent | Inutilisable |
| Bridge one-shot | UX import | Bloque automation | — |
| Pas de cloud | OK local-first | Demande sync multi-Mac | Produit 2.0 |
| Swift enum fermé | OK 2 providers | Friction N providers | — |

---

## 7. Améliorations implémentées (cette PR)

### 7.1 `UnsupportedSchemaVersionError`

**Avant :** fichier schema_version=2 lu par app v1 → playlists effacées silencieusement.  
**Après :** exception explicite, données préservées sur disque.

### 7.2 `get_playlist` optimisé

**Avant :** `list_playlists()` triait tout le catalogue à chaque lookup.  
**Après :** scan direct sans tri — gain immédiat sur écrans détail/sync.

### 7.3 Snapshots verrouillés

**Avant :** `temp.replace()` sans `fcntl` — course si 2 processus bridge importent le même snapshot.  
**Après :** `locked_json_document` — cohérent avec managed playlists.

### 7.4 Guards architecture

`tests/test_layer_architecture.py` empêche :
- nouveaux imports UI dans `integration/ports` (hors transitional)
- imports provider dans sync core (hors apply)
- imports `bridge_runtime` dans observability

### 7.5 Import `ProviderPlaylistWritePort`

Correction analyse statique dans `action_executor.py` — pas de changement comportemental.

---

## 8. Roadmap architecture recommandée (sans spéculation)

| Phase | Action | Déclencheur |
|-------|--------|-------------|
| **1.0.x** | Guards, correctifs persistance, doc | ✅ Cette PR |
| **1.1** | Extraire `domain/` (types SSOT) | Premier plugin tiers ou SQLite spike |
| **1.2** | Facades bridge + process persistant | Métrique latence import > seuil |
| **1.3** | Aligner plan/apply sync | Validation Music.app mirror/reorder |
| **2.0** | SQLite backend, HTTP API, rules engine | Epic Resonance 2.0 (TARGET_ARCHITECTURE) |
| **2030** | Resonance Services (cloud) | ADR dédié quand palier activé |

---

## 9. Note sur la qualité architecturale

### Score : **7,5 / 10**

| Critère | Note | Commentaire |
|---------|------|-------------|
| Modularité | 8/10 | Packages clairs, sync engine exemplaire |
| Couplage | 6/10 | Inversion UI ↔ integration |
| Testabilité | 8/10 | 534 tests, guards AST, E2E en PR séparée |
| Évolutivité 2.0 | 7/10 | Protocols présents, domaine mal placé |
| Documentation | 9/10 | ADR, TARGET_ARCHITECTURE, vision 2030 |
| Performance | 7/10 | OK local-first MVP, limites JSON connues |
| OSS readiness | 8/10 | LICENSE, CI, gouvernance, limitations documentées |

### Points forts

- Moteur de sync provider-neutral avec tests d'architecture enforceables
- Séparation claire Music Providers / Resonance Services (vision long terme)
- Ports d'import canoniques et registry extensible
- Persistance atomique et idempotence sync
- Documentation architecturale rarement vue à ce stade de produit

### Limites restantes

- Agrégats domaine sous namespace UI
- Écart plan/apply sync sur actions avancées
- `backend.py` god object et bridge one-shot
- Triple stack import
- Scale JSON limitée sans migration SQLite
- Plugins : fondations sans runtime

### Pour atteindre un niveau OSS de référence (9/10)

Logiciels de référence (ex. **Immich**, **Home Assistant**, **Zed**) partagent :

1. **Domaine pur** sans dépendance surface — à faire via `domain/`
2. **API stable versionnée** — bridge OK, HTTP localhost à ajouter en 2.0
3. **Migrations données testées** — commencer par SQLite + tests migration
4. **Guards CI architecture** — étendre (fait partiellement ici)
5. **Contributing path clair pour plugins** — loader + exemple plugin minimal
6. **Benchmarks perf** — seuils documentés avec tests de charge

Resonance est **au-dessus de la moyenne** pour un produit v1.0 solo/small-team, et **en dessous** des leaders OSS sur l'isolation domaine et l'extensibilité runtime. La trajectoire documentée (TARGET_ARCHITECTURE, ADR-022) ferme cet écart sans réécriture.

---

*Audit réalisé juillet 2026 — Resonance v1.0.0*
