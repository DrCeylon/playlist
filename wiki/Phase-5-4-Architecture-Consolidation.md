# Phase 5.4 — Consolidation de l'architecture Resonance

*Analyse Solution Architect — juillet 2026*

Document de référence pour la transition Resonance → moteur de playlists multi-provider. **Aucun changement de comportement produit** ; préparation documentaire et roadmap uniquement.

**Documents liés :** [ADR-013](../docs/architecture/ADR-013-multi-provider-platform-vision.md), [vision.md](../docs/architecture/vision.md), [Phase 5.3.3 Decision](Phase-5-3-3-Acquisition-Decision.md)

---

## 1. Cartographie de l'architecture actuelle

### Couches (état réel)

```text
┌─────────────────────────────────────────────────────────────┐
│  Resonance macOS (Swift) — ResonanceMac / ResonanceCore     │
│  ViewModels, BridgeClient, Import UX, Historique            │
└────────────────────────────┬────────────────────────────────┘
                             │ JSON-RPC (engine_bridge)
┌────────────────────────────▼────────────────────────────────┐
│  playlist_builder/ui/ — DTOs, bridge, thèmes, historique    │
│  (garde-fous : pas d'import apple_music)                    │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  playlist_builder/app/ — factory, settings, use cases         │
│  bridge_runtime/ ← FUITE MAJEURE (import_stream Apple)      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  playlist_builder/integration/gateway/ — IntegrationGateway │
│  registry (générique) + duck-typing applescript (fuite)       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  playlist_builder/integration/apple_music/ — Provider Apple │
│  resolver, delivery, acquisition, applescript_client        │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  playlist_builder/canonical/ — modèle + ports (neutre)      │
│  playlist_builder/infrastructure/cache/ — IdentityCache     │
│  playlist_builder/scoring/ — moteur de score (neutre)       │
│  playlist_builder/planning/ + discovery/ + session/ — gen     │
└─────────────────────────────────────────────────────────────┘
```

### Bounded contexts

| Contexte | Modules | Rôle |
|----------|---------|------|
| **Composition** | `planning/`, `session/`, `discovery/` | Génération playlist depuis seeds/contraintes |
| **Catalog** | `integration/*/catalog*`, `catalog/` | Recherche candidats externes |
| **Delivery** | `integration/*/delivery*`, `import_service` | Résolution + livraison playlist |
| **Application** | `app/`, `cli/`, `ui/bridge` | Orchestration, bridge Resonance |
| **Produit** | `apps/resonance/` | Shell macOS SwiftUI |

---

## 2. Dépendances Apple Music par couche

### Synthèse quantitative (fichiers touchés)

| Couche | Fichiers Apple intentionnels | Fuites / couplage | Verdict |
|--------|------------------------------|-------------------|---------|
| **Core** | ~1 (`ProviderId.APPLE_MUSIC`) | **~10** | ⚠️ Fuites legacy |
| **Provider** | **~24** | 0 | ✅ Correct |
| **UI** | ~6 (thèmes, copy) | **~10** (defaults) | ⚠️ Produit v1 |
| **Infrastructure** | 0 | **~8** | ⚠️ Gateway + bridge |
| **Tests** | **~22** Python + ~10 Swift | ~5 | ✅ Attendu |

### Core — fuites à corriger (cartographie, pas implémentation)

| Fichier | Symbole / problème | Gravité |
|---------|-------------------|---------|
| `core/applescript.py` | `run_applescript`, osascript | P1 — hors core |
| `core/platform.py` | `require_macos(feature="Apple Music")` | P2 |
| `music/client.py` | `MusicClient`, `persistent_id`, `AppleMusicResolutionStatus` | P1 — legacy facade |
| `music/musickit_client.py` | API Apple MusicKit | P2 — expérimental |
| `catalog/apple_search.py` | `AppleCatalogSearch` | P1 — hors `integration/` |
| `discovery/itunes_provider.py` | Import mapper Apple | P1 |
| `discovery/adapters.py` | `discovery_candidate_to_planning` depuis mapper Apple | P1 |
| `discovery/models.py` | Default `ProviderId.APPLE_MUSIC` | P2 |
| `discovery/providers.py` | Hardcode Apple provider_id | P2 |

**Ce qui est propre dans le Core :** `canonical/*`, `scoring/*`, `infrastructure/cache/identity_cache.py`, `planning/*` (sauf commentaires).

### Provider — périmètre correct (`integration/apple_music/`)

20 modules dont : `resolver.py`, `delivery.py`, `applescript_client.py`, `library_acquisition.py`, `acquisition_policy.py`, `catalog_gateway.py`, `itunes_client.py`, `gateway.py`, `import_service.py`, `autocomplete_gateway.py`, etc.

Concepts Apple **légitimes** ici : `persistent_id`, `AppleMusicTrack`, `duplicate to Library`, MusicKit POC.

### UI — Python (`playlist_builder/ui/`)

| Élément | Nature | Action future |
|---------|--------|---------------|
| `default_provider_options()` — seul Apple actif | Produit v1 | Activer Spotify/YouTube quand providers prêts |
| `preferences.py` — chemins `apple_music_identity.json`, `itunes_catalog.json` | Config par défaut | Renommer générique ou par provider |
| Thèmes `apple_music_light/dark` | Cosmétique | Conserver ou rebrander « Resonance » |
| `history/serialization.py` — strip `persistent_id` | ✅ Bonne pratique | Garder |
| Garde AST `test_ui_shared_guard.py` | ✅ | Étendre si nouveaux packages |

### UI — Swift (`apps/resonance/`)

| Zone | Couplage Apple |
|------|----------------|
| `DefaultProviders`, `.appleMusic` defaults | Produit — acceptable v1 |
| Copy « Music.app », « Apple Music » | UX — à généraliser (« bibliothèque du fournisseur ») |
| `ManualAcquisitionCard`, `MusicAppLink` | Spécifique Apple — rester dans composants provider-scoped |
| `ProviderNeutralGuardTests` | ✅ Empêche `persistent_id` dans ViewModels |

### Infrastructure — fuites critiques

| Fichier | Fuite |
|---------|-------|
| **`app/bridge_runtime/import_stream.py`** | `ProviderId.APPLE_MUSIC` hardcodé ; `resolver._applescript` ; `AppleMusicResolutionStatus` ; diagnostics Music.app |
| **`integration/gateway/service.py`** | `getattr(import_service, "applescript")` ; `load_playlist_keys` ; default `APPLE_MUSIC` |
| `app/factory.py` | Seul gateway Apple enregistré ; accessor `apple_music()` |
| `app/use_cases/autocomplete_search.py` | Import direct `AppleAutocompleteGateway` |
| `app/bridge_runtime/retry_import.py` | `AppleMusicResolutionStatus`, pas de manual gate |
| `app/bridge_runtime/manual_gate.py` | Import lazy `catalog_ids` (Apple URLs) |
| `app/settings.py` | Chemins cache Apple par défaut |

### Tests — répartition

| Catégorie | Fichiers (~) | Rôle |
|-----------|--------------|------|
| Apple provider | 11 `test_apple_music_*` | Resolver, delivery, acquisition, script |
| Acquisition 5.3 | 4 `test_acquisition_*`, `test_manual_*` | Politique production ADR-012 |
| Core neutre | ~20 | Canonical, scoring, gateway, planning |
| UI / bridge | ~12 | Contrats JSON-RPC, garde-fous |
| Swift | 22 | ViewModels, bridge, thèmes, guards |
| **Total** | **~352 pytest + ~104 Swift** | |

---

## 3. Points où Apple « fuit » dans le Core

### Tableau des fuites par type

| Type | Exemples | Couche réelle | Cible |
|------|----------|---------------|-------|
| **Types** | `AppleMusicResolutionOutcome`, `AppleMusicTrack` | Provider ✅ | Ne pas importer hors provider |
| **Enums** | `AppleMusicResolutionStatus` dans `import_stream`, `retry_import` | App ❌ | `ImportStatus` / `ResolutionDecision` canoniques |
| **Classes** | `MusicClient`, `AppleCatalogSearch` | Core legacy ❌ | Déplacer ou déprécier |
| **Constantes** | `ITUNES_SEARCH_URL`, poll delays acquire | Provider ✅ | — |
| **Cache** | `apple_music_identity.json` path | Settings | `identity_cache.json` ou `{provider}_identity.json` |
| **Interfaces** | `LibraryResolvePort` non implémenté ; resolver monolithique | Provider | Adapter `AppleMusicResolver` → port |
| **Événements** | `manual_acquisition_required` avec `catalog_url` Apple | Bridge | OK si champs optionnels provider-agnostiques |
| **Modèles** | `persistent_id` sur outcomes provider | Provider ✅ | Jamais dans DTO UI (déjà filtré) |

### Architecture cible d'isolation (cartographie)

```text
                    ┌─────────────────────┐
                    │  ProviderImportPort │  ← nouveau (streaming + manual)
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
  LibraryResolvePort    CatalogAcquisitionPort   PlaylistDeliveryPort
  (library search)      (acquire + manual)        (sync playlist)
         │                     │                     │
         └─────────────────────┴─────────────────────┘
                               │
                    AppleMusicProviderGateway
                    (seul endroit AppleScript)
```

**Règle d'or (vision.md) :** zéro import `integration.apple_music` hors `integration/`, `app/factory.py` (composition root), et tests provider.

---

## 4. Revue des ADR

| ADR | Titre | Validité | Action |
|-----|-------|----------|--------|
| **005** | Apple delivery + identity cache | ✅ Valide | Mineur : noter `LibraryResolvePort` toujours non extrait |
| **007** | Catalog fallback advisory | ✅ Valide | Inchangé (ADR-012 le confirme) |
| **008** | Application platform + acquisition | ⚠️ Partiel | **Amender §2** : workflow auto S2 remplacé par ADR-012 |
| **009** | Acquisition workflow | ⚠️ Partiel | Marquer étapes S2 **supplantées** ; garder historique manual |
| **010** | Phases 2–3 completion | ✅ Valide | Gateway pattern prêt multi-provider |
| **011** | Cross-platform UI | ✅ Valide | Mettre à jour statut Phase 4 (implémenté) ; risques lifecycle bridge |
| **012** | Production acquisition policy | ✅ **Autorité production** | Ajouter à README architecture |
| **013** | Multi-provider vision | 🆕 Proposé | Ce document + ADR-013 |

### Nouvelles ADR futures (multi-provider)

| ADR | Sujet | Quand |
|-----|-------|-------|
| ADR-014 | Spotify provider — auth, URI, delivery API | Avant implémentation Spotify |
| ADR-015 | YouTube Music — ID model, acquisition | Avant implémentation YT |
| ADR-016 | ProviderImportPort — streaming import contract | Phase 5.5–5.6 |
| ADR-017 | Cross-provider playlist « open in X » UX | Produit |

---

## 5. Roadmap d'architecture (petites phases livrables)

Chaque phase : **compatible**, **testable**, **sans régression UX**.

| Phase | Objectif | Livrable | Risque |
|-------|----------|----------|--------|
| **5.4** ✅ | Consolidation documentaire | Ce rapport, ADR-013, index ADR | Aucun (docs) |
| **5.5** | Extraire `ProviderImportPort` | Interface + Apple adapter ; `import_stream` délègue au port | Moyen — régression import |
| **5.5b** | Supprimer `_applescript` du bridge | `import_stream` ne touche plus resolver privé | Moyen |
| **5.6** | Gateway générique | `prepare_incremental_import` via port, pas duck-typing | Faible |
| **5.7** | Discovery découplé | `ITunesCandidateProvider` → `CatalogSearchPort` uniquement | Faible |
| **5.8** | Legacy cleanup | Déprécier `music/client.py`, `catalog/apple_search.py` | Faible |
| **6.0** | `ProviderIdentityRegistry` façade | Wrapper IdentityCache + API Core documentée | Faible |
| **6.1** | Provider stub Spotify | Gateway vide + tests registry + ADR-014 | Faible |
| **6.2** | UI multi-provider | Sélecteur provider actif ; copy neutre | UX — pas de régression Apple |
| **7.0** | Spotify MVP | Resolve + deliver (pas acquisition complexe) | Élevé — OAuth |
| **7.x** | YouTube Music | ADR-015 + provider package | Élevé |

**Principe small commits :** chaque phase = 1–3 PRs max, tests de garde existants préservés.

---

## 6. IdentityCache — analyse complète

### Modèle actuel

```text
Clé : identity::{provider_id}::{canonical_track_identity_key}
Valeur : { provider_id, external_id, confidence, resolved_at }
```

- **Un** `external_id` par couple `(canonical_key, provider_id)`.
- `external_id` est opaque (PID Apple, URI Spotify futur).
- `ProviderIdentity.metadata` existe mais peu utilisé.

### Capacités multi-provider

| Besoin | Support actuel | Suffisant ? |
|--------|----------------|-------------|
| Plusieurs providers | ✅ Clés namespacées par `ProviderId` | Oui |
| Plusieurs IDs **même provider** pour un morceau | ❌ `put` écrase | Non — cas rare (remasters) ; v2 possible |
| Sync cross-provider | ❌ Aucune logique | Non — hors scope cache |
| Résolution croisée | ❌ Pas de lien Apple↔Spotify | Non — besoin registry sémantique séparé |
| Acquisition en attente | ❌ Pas d'état `pending` | Partiel — session import bridge séparée |

### Architecture cible proposée (non implémentée)

```text
ProviderIdentityRegistry (façade Core)
  ├── get_identity(track, provider) → ProviderIdentity | None
  ├── put_identity(track, identity)
  ├── list_providers(track) → list[ProviderId]  # futur
  └── invalidate(track, provider)

IdentityCache (inchangé — persistence JsonCache)
```

**Recommandation :** ne pas changer le schéma JSON avant Spotify. Le modèle actuel **suffit** pour N providers indépendants. La résolution croisée (ISRC, MusicBrainz) est un **service catalogue** futur, pas une extension IdentityCache.

---

## 7. IntegrationGateway — analyse complète

### Déjà réutilisable ✅

| Méthode | Neutralité |
|---------|------------|
| `import_playlist(playlist, provider_id=...)` | ✅ Route via registry |
| `search_catalog(request, provider_id=...)` | ✅ |
| `flush_caches(provider_id=...)` | ✅ Structure générique |
| `ProviderGatewayRegistry` | ✅ |

### Encore Apple-specific ❌

| Point | Détail |
|-------|--------|
| `prepare_incremental_import` | `getattr(import_service, "applescript")` + `load_playlist_keys` |
| Defaults | Tous les `provider_id` default `APPLE_MUSIC` |
| `import_service` duck-typing | Attribut non port ; `AppleMusicImportService` only |
| Factory | Un seul gateway enregistré |

### Évolution proposée

```python
# Futur — Protocol sur ProviderGateway
class IncrementalImportPort(Protocol):
    def prepare_playlist(self, name: str, *, allow_duplicates: bool) -> IncrementalImportContext: ...
```

`IntegrationGateway` n'appelle que des ports du `ProviderGateway` enregistré.

**Écart actuel majeur :** le bridge Resonance **contourne** `IntegrationGateway.import_playlist` via `import_stream.py` pour le streaming d'événements. La consolidation passe par **ProviderImportPort** (Phase 5.5), pas par l'extension du gateway sync existant.

---

## 8. Revue des tests

### Tests potentiellement obsolètes / à reclasser

| Fichier | Note |
|---------|------|
| `test_apple_music_acquire_script.py` | Valide **LEGACY_EXPERIMENTAL** S2 uniquement — garder, tagger `legacy` |
| `test_apple_music_library_acquisition.py` | Flow resolver complet — chevauche `test_acquisition_production_policy` |
| `test_music_client.py` | Legacy facade — déprécier avec `music/client.py` |
| `test_musickit_client.py` | POC — garder hors CI critique |

### Doublons identifiés

| Zone | Fichiers | Recommandation |
|------|----------|----------------|
| Cache hit resolver | `test_apple_music_resolver`, `test_acquisition_production_policy` | Garder les deux (couches différentes) |
| Acquisition manual | `test_apple_music_manual_acquisition`, `test_acquisition_production_policy` | Consolider **à terme** en 1 suite policy + 1 suite resolver |
| Scoring/normalisation | `test_resolver`, `test_scoring`, `test_core` | Acceptable — modules différents |
| Thème | Python + Swift + shell | **Intentionnel** (contrat cross-runtime) |

### Zones insuffisamment couvertes (priorité architecture)

| Gap | Priorité | Test proposé |
|-----|----------|--------------|
| Bridge import sans fuite Apple types | P1 | `test_import_stream_provider_port.py` (post 5.5) |
| Gateway `prepare_incremental` sans applescript | P1 | Mock `IncrementalImportPort` |
| Registry multi-provider | P1 | 2 gateways fake dans `test_integration_gateway` |
| Identity cache E2E gateway | P2 | Import mocké 2× même track |
| Bridge subprocess lifecycle | P2 | ADR-011 risque — hors scope immédiat |
| `retry_import` + manual gate | P2 | Aligner retry sur production policy |

### Principe

**Ne pas ajouter des centaines de tests.** Privilégier :

1. Garde-fous existants (`test_ui_*_guard`, `ProviderNeutralGuardTests`)
2. Tests policy ADR-012 (`test_acquisition_production_policy`)
3. Un test d'intégration bridge par phase de refactor (5.5+)

---

## 9. Dette technique priorisée

### P0 — Bloquant (multi-provider / stabilité)

| ID | Élément | Impact | Risque | Coût | Bénéfice |
|----|---------|--------|--------|------|----------|
| P0-1 | `import_stream.py` bypass gateway + `_applescript` | Bridge non portable | Régression import à chaque provider | M | Déblocage Spotify/YT |
| P0-2 | `IntegrationGateway.prepare_incremental_import` duck-typing applescript | Gateway faux-générique | Second provider impossible | S | Contrat clair |
| P0-3 | ADR-008 §2 obsolète (S2 auto) | Doc trompeuse | Mauvaises décisions dev | XS | Alignement équipe |

### P1 — Important

| ID | Élément | Impact | Risque | Coût | Bénéfice |
|----|---------|--------|--------|------|----------|
| P1-1 | `core/applescript.py` dans core | Violation vision.md | Confusion couches | S | Core pur |
| P1-2 | `discovery/` → mapper Apple | Génération couplée Apple | Spotify discovery cassé | M | Catalog port unique |
| P1-3 | `autocomplete_search` → Apple gateway | Feature non portable | — | S | Multi-provider autocomplete |
| P1-4 | `retry_import.py` sans manual gate | Historique retry ≠ production | UX incohérente | S | Parité Nouvelle Playlist / Historique |
| P1-5 | `LibraryResolvePort` non extrait | ADR-005 follow-up ouvert | Mock resolver difficile | M | Testabilité |
| P1-6 | Tests acquisition redondants | CI lente, maintenance | Flaky mocks | S | Clarté |

### P2 — Confort

| ID | Élément | Impact | Risque | Coût | Bénéfice |
|----|---------|--------|--------|------|----------|
| P2-1 | Legacy `music/client.py`, `catalog/apple_search.py` | Deux chemins d'import | — | M | Simplification |
| P2-2 | UI defaults `.appleMusic` partout | Perception « app Apple » | — | M | Image produit |
| P2-3 | Thèmes `apple_music_*` | Branding | — | S | Identité Resonance |
| P2-4 | Chemins cache `itunes_catalog.json` | Nommage | — | XS | Clarté config |
| P2-5 | PR10 resolution trace générique | ADR-006/010 | — | L | Diagnostics neutres |

*Coût : XS < 1j, S = 1–2j, M = 3–5j, L > 1 semaine (effort technique, pas calendaire).*

---

## 10. Spotify — premiers points nécessaires (analyse seule)

### Interfaces

| Port | Responsabilité Spotify |
|------|------------------------|
| `CatalogSearchPort` | Web API search `track`, `artist` |
| `LibraryResolvePort` | `GET /me/tracks`, `GET /me/playlists` |
| `PlaylistDeliveryPort` | `POST /playlists`, `POST /playlists/{id}/tracks` |
| `ProviderAcquisitionPort` *(nouveau)* | Ajout bibliothèque utilisateur (si API le permet) ou flow OAuth |
| `ProviderImportPort` *(nouveau)* | Stream événements + auth refresh |

### Responsabilités provider

- OAuth 2.0 PKCE (connexion compte utilisateur)
- Mapping `CanonicalTrack` → recherche Spotify → `spotify:track:{id}`
- Persistance `external_id` = URI Spotify dans IdentityCache
- Rate limiting API (headers `Retry-After`)
- **Pas d'AppleScript** — acquisition = API ou manuel Spotify client

### Impacts

| Zone | Impact |
|------|--------|
| `ProviderId.SPOTIFY` | Déjà dans enum — activer dans `default_provider_options` |
| `factory.py` | `build_spotify_gateway()` + registry |
| UI Swift | OAuth flow, connexion compte, copy neutre |
| ADR | **ADR-014** obligatoire avant code |
| Tests | Fake gateway Spotify dans `test_integration_gateway` |

---

## 11. YouTube Music — premiers points nécessaires (analyse seule)

### Spécificités

- Pas d'API publique équivalente Spotify pour playlists utilisateur
- Identifiant cible : `videoId` YouTube Music
- Acquisition : quasi-toujours **manuelle** ou API YouTube Data (hors scope Music)
- Delivery : API limitée — possiblement **export** ou deep link plutôt que sync playlist

### Interfaces minimales

| Port | Faisabilité |
|------|-------------|
| `CatalogSearchPort` | YouTube Data API search (quota) |
| `LibraryResolvePort` | ⚠️ Très limité sans API officielle Music |
| `PlaylistDeliveryPort` | ⚠️ Probablement « playlist links » pas sync |
| `ProviderAcquisitionPort` | Manuel / navigateur |

### Impacts

- ADR-015 dédié — **ne pas réutiliser** le modèle Apple acquisition
- Provider probablement **catalog + export** avant « full delivery »
- IdentityCache : `external_id` = video ID ou URL canonique

---

## 12. Vision produit — analyse critique

### Aujourd'hui : perception « client Apple Music »

| Signal utilisateur | Cause technique |
|--------------------|-----------------|
| Seul provider actif | `DefaultProviders` Apple seul |
| Copy « Music.app », « Apple Music » | Strings hardcodées Swift + bridge diagnostics |
| Acquisition manuelle Music.app | Workflow ADR-012 légitime mais Apple-only |
| Thèmes « Apple Music inspiration » | Cosmétique |
| Génération via iTunes catalog | `ITunesCandidateProvider` seul actif |

### Cible : « moteur universel de playlists »

| Pilier | État | Gap |
|--------|------|-----|
| **Composition provider-neutral** | ✅ `CanonicalPlaylist`, scoring, planning | Discovery encore iTunes |
| **Delivery provider-pluggable** | ⚠️ Gateway existe, bridge bypass | import_stream |
| **Identité canonique stable** | ✅ `identity_key`, ISRC-ready | — |
| **Multi-connection comptes** | ❌ | OAuth Spotify, etc. |
| **Même playlist → plusieurs apps** | ❌ | Produit + registry |
| **UX acquisition** | ✅ Pattern manual gate portable | Copy et deep links Apple |

### Recommandation produit

1. **Court terme :** conserver Apple comme seul provider **actif**, mais communiquer en interne « Resonance Engine + Apple Provider ».
2. **Moyen terme :** écran « Fournisseurs connectés » (Apple actif, Spotify « bientôt ») — pas de fausse promesse YT.
3. **Ne pas** masquer le workflow manuel Apple — il est honnête et portable comme **pattern** `ProviderAcquisitionInterrupted`.
4. **Renommer progressivement** les surfaces utilisateur : « Importer dans la bibliothèque » vs « Importer dans Apple Music » une fois second provider actif.

---

## 13. Synthèse exécutive

| Question | Réponse |
|----------|---------|
| Le Core est-il prêt multi-provider ? | **Structurellement oui** (`canonical/`, ports, IdentityCache). **Runtime non** (bridge + discovery). |
| IdentityCache suffit-il ? | **Oui** pour N providers indépendants. **Non** pour équivalence cross-provider. |
| IntegrationGateway suffit-il ? | **Partiellement** — import sync oui ; incremental + streaming non. |
| ADR cohérents ? | Oui, avec **ADR-008/009 à amender** et **ADR-012/013** comme références production + vision. |
| Prochaine étape technique ? | **Phase 5.5** — `ProviderImportPort`, supprimer `_applescript` du bridge. |
| Prochaine étape produit ? | Documentation + ADR-014 Spotify avant toute implémentation. |

---

## Fichiers de cette phase

| Fichier | Rôle |
|---------|------|
| `wiki/Phase-5-4-Architecture-Consolidation.md` | Ce rapport |
| `docs/architecture/ADR-013-multi-provider-platform-vision.md` | Décision vision multi-provider |
| `docs/architecture/README.md` | Index ADR mis à jour |

**Aucun changement de workflow production, performances, ou UX** dans cette phase.
