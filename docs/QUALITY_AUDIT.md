# Resonance — Quality Audit (Staff Engineer)

**Date:** July 2026 · **Scope:** Python engine, Swift macOS app, bridge, CI, OSS readiness  
**Posture:** All functional phases complete — audit prépare un dépôt open source mature.

---

## Executive summary

| Dimension | Grade | Verdict |
|-----------|-------|---------|
| Architecture (intent) | B+ | ADRs solides, ports/registry réels, sync engine provider-neutral |
| Architecture (execution) | C+ | Couplage DTO UI↔domaine, god objects bridge, triple stack import |
| Tests | B | ~490 tests Python, guards archi — lacunes bridge résolues partiellement |
| Security | B− | Bonnes intentions ADR-015 ; garde-fous maintenant branchés sur sorties auth |
| OSS readiness | B− | LICENSE + CONTRIBUTING ajoutés ; i18n et README à repositionner |
| Swift UX layer | B | Coordinator solide ; DI unifiée en cours |
| CI | B | Python CI + triggers bridge cross-lang |

**Forces:** discipline de test, séparation plan/apply sync, repository local SSOT, documentation ADR riche.  
**Risques croissance:** JSON persistence scale, bridge one-shot, domain layer inversion, Apple-centric defaults.

---

## 1. Revue SOLID

| Principe | Constat | Exemple |
|----------|---------|---------|
| **S** Single Responsibility | Violé (bridge) | `RuntimeEngineBridgeBackend` — génération, import, history, sync, auth |
| **O** Open/Closed | Partiel | `ProviderGatewayRegistry` extensible ; `factory.get_provider_import_port` fermé par `if Apple` |
| **L** Liskov | OK | Ports mockables, tests avec fakes |
| **I** Interface Segregation | Violé (Swift) | `PythonEngineBridgeService` implémente 7 protocols |
| **D** Dependency Inversion | Violé (domaine) | `app/playlist_sync` importe `ui/shared/dto` |

**Recommandation structurante (non appliquée — changement large) :** extraire `playlist_builder/domain/` et faire de `ui/shared/dto` un adaptateur Swift/bridge.

---

## 2. Clean Architecture

```
[UI Swift] → [Bridge JSON] → [bridge_runtime] → [use cases / playlist_sync] → [ports] → [integration]
```

**Fuites actuelles :**
- DTOs « entités » dans `ui/shared/dto/` consommés par le domaine.
- `import_stream.py` (~750 LOC) mélange orchestration, événements bridge, Apple runtime.
- CLI `import_playlist` et bridge import ne partagent pas le même orchestrateur.

**Aligné :** `plan_sync` / `apply_sync` / `resolve_sync_conflicts` séparés ; validator avant apply ; audit `PlaylistSyncOperation`.

---

## 3. DDD

| Bounded context | Modèle | Foyer |
|---------------|--------|-------|
| Génération | Seeds, scoring, sections | `scoring/`, `generation/` |
| Import acquisition | Track outcomes, manual flow | `import_stream`, `ManualAcquisitionWorkflow` |
| Playlist locale | `ManagedPlaylistDetail`, versioning | `playlist_library/` |
| Sync | Plan, conflits, opérations | `playlist_sync/` |
| Providers | Gateway, capabilities | `integration/` |

**Anti-patterns :** `ProviderId` Apple par défaut partout ; stub `sync_managed_playlist` encore exposé ; langage ubiquitaire FR/EN mélangé dans erreurs bridge.

---

## 4. Architecture hexagonale

| Port | Adapter(s) | État |
|------|------------|------|
| `ProviderImportPort` | Apple | Gelé, production |
| `ProviderPlaylistReadPort` | Apple, YouTube | OK |
| `ProviderPlaylistWritePort` | Apple | Partiel (append_only fiable) |
| `ProviderAuthPort` | YouTube | Expérimental |
| `ManagedPlaylistRepository` | JSON | SSOT, verrouillé (audit) |

**Le moteur sync ne connaît pas les providers** — validé par `tests/test_sync_architecture.py`.

---

## 5. Revue Python

| Aspect | Note |
|--------|------|
| Typage | Bon (`from __future__ import annotations`, dataclasses) |
| Tests | Pytest exhaustif, arch guards |
| Duplication | Deserializers snapshot/playlists tripliqués dans bridge |
| Persistence | JSON + flock ; pas SQLite |
| Sécurité | `secrets.py` ; scrub sorties auth |
| Packaging | `pyproject.toml` propre, extras `[youtube]` |

---

## 6. Revue Swift / SwiftUI

| Aspect | Note |
|--------|------|
| Packages | Core / Design / Mac — bon découpage |
| Coordinator | `AppWorkflowCoordinator` — workflow génération/import |
| ViewModels | Délégation services ; éviter logique métier ✅ |
| DI | Unifié via `engineBridge` (Historique, Labo corrigés) |
| Navigation | `NavigationSplitView` + `NavigationStack` |
| Tests | ViewModels mockés ; guards symboles |

**Amateur patterns restants :** `print` logging bridge ; `fatalError` thèmes ; bridge one-shot.

---

## 7. Bridge & DTO

- **28 commandes** — parité Python/Swift testée (`BridgeCommand.allCases`).
- **Correction P0 :** `resolve_sync_conflicts` utilisait un appel `get_managed_playlist` invalide.
- **DTO enrichis** Phase 6.7 — conflits UI-ready.
- **Drift risque :** validation génération Swift locale vs Python `validate_generation_request`.

---

## 8. Ce qui semblait amateur (et statut)

| Item | Statut audit |
|------|--------------|
| Bridge commande cassée (resolve) | **Corrigé** |
| CI Python absente | **Corrigé** |
| Pas de LICENSE | **Corrigé** (MIT) |
| TECHNICAL_DEBT dupliqué / obsolète | **Corrigé** |
| JSON write sans lock | **Corrigé** |
| Secrets guard mort | **Corrigé** (sorties auth) |
| 3 bridges Swift isolés | **Corrigé** (History, Diagnostics) |
| Carte « architecture » dans UI | Phase 6.8 (si mergée) |
| God `backend.py` | Documenté — refactor futur |
| DTOs dans `ui/` | Documenté — refactor futur |

---

## 9. Ce qui empêchera de grandir (non corrigé — roadmap)

1. **Bridge one-shot** — latence, pas de pool process.
2. **JSON repository** — O(n) full-file, pas de requêtes partielles.
3. **Import stack triple** — risque divergence Apple.
4. **Apply sync partiel** — planner émet actions non exécutables.
5. **i18n** — français uniquement.
6. **README** — titre encore « Apple Music Playlist Builder ».
7. **Domain/DTO inversion** — friction contributeurs providers.

---

## 10. Correctifs appliqués (cette PR)

| Fichier / zone | Changement | Justification |
|----------------|------------|---------------|
| `backend.resolve_sync_conflicts` | Charge `ManagedPlaylistDetail` via `self.get_managed_playlist` | Bug runtime P0 |
| `backend.import_playlist_stream` | Passe `sync=` au stream | Paramètre documenté ignoré |
| `infrastructure/atomic_json.py` | Verrou `fcntl` + RMW atomique | Race conditions JSON |
| `json_repository.py`, sync ops repo | `upsert` atomique | Perte de données concurrente |
| `provider_platform.py` | `assert_bridge_safe_mapping` sur comptes | ADR-015 |
| `.github/workflows/python-ci.yml` | CI pytest Linux | Gate qualité OSS |
| `resonance-macos.yml` | Trigger sur paths bridge | Contrat cross-lang |
| Swift History/Diagnostics | `workflow.engineBridge` partagé | État cohérent |
| `BridgeCommand.allCases` + tests | Parité 28 commandes | Drift contractuel |
| `LICENSE`, `CONTRIBUTING.md` | OSS baseline | Adoption |
| `Makefile check-all` | Gate locale documentée | DX |
| Tests | resolve bridge, atomic json, command contract | Régression |

---

## 11. Métriques post-audit

```
pytest -q  → 490 passed, 1 skipped
```

Swift : exécuter `apps/resonance/scripts/build.sh` sur macOS CI.

---

## Références

- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- ADR-013 à ADR-018
- [phase-6-provider-platform.md](product/phase-6-provider-platform.md)
