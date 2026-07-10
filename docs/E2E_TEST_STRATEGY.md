# Stratégie de tests End-to-End — Resonance v1.0

Ce document définit la stratégie de tests d'intégration et End-to-End (E2E) pour Resonance. Il complète la couverture unitaire existante (~530 tests) en vérifiant que les briques fonctionnent **ensemble** via le pont JSON-RPC (`JsonRpcEngineBridge` → `RuntimeEngineBridgeBackend`).

## Objectifs

| Objectif | Approche |
|----------|----------|
| Déterminisme | Harness isolé (`tmp_path`), fakes injectés, pas de réseau ni Music.app |
| Reproductibilité | Données d'exemple fixes (`sample_remote_playlist_dict`), bus observability réinitialisé |
| Indépendance | Chaque test crée son propre harness via fixture `e2e_harness` |
| Rapidité | E2E ciblés (~0,7 s pour 27 tests dans `tests/e2e/`) ; suite complète ~2 min |
| CI | `python -m pytest -q` sur Ubuntu ; macOS workflow séparé pour Apple réel |

## Pyramide de tests

```
                    ┌─────────────────┐
                    │  E2E (7 marqués) │  Parcours utilisateur via bridge
                    ├─────────────────┤
                    │ Integration (~4+) │  Multi-modules, mocks/fakes
                    ├─────────────────┤
                    │  Unit (~547)     │  Modules isolés, logique pure
                    └─────────────────┘
```

### Définitions

| Niveau | Périmètre | Exemple |
|--------|-----------|---------|
| **Unitaire** | Une fonction/classe, dépendances mockées | `test_playlist_sync_planning.py` |
| **Intégration** | Plusieurs modules, fakes pour I/O externes | `test_resolve_sync_bridge.py`, import stream mocké |
| **E2E** | Commande bridge complète → persistance + événements | `tests/e2e/test_user_journey_sync.py` |

## Architecture du harness E2E

Fichier : `tests/e2e/harness.py`

```
tmp_path
  ├── cache/          (catalog, identity — désactivé)
  ├── data/
  │   ├── managed_playlists.json
  │   ├── sync_operations.json
  │   ├── snapshots/
  │   └── provider_auth/
  └── FakeSyncGateway (remplace Apple pour sync)
      └── FakeWritePort (enregistre upsert/remove, simule échecs)
```

- **Registry** : `FakeSyncGateway` (Apple sync) + `YouTubeMusicGateway` (réel, sans auth → experimental)
- **Observability** : `reset_default_bus()` à chaque harness
- **Point d'entrée** : `E2EHarness.call(command, params)` → messages JSON-RPC

## Matrice des scénarios utilisateur

Source machine-readable : `tests/e2e/scenarios.py` (`USER_SCENARIOS`).

Légende : ✅ automatisé | ⏸ documenté, non automatisé (CI Linux)

---

### Import

| ID | Domaine | Préconditions | Actions | Résultats attendus | Données persistées | Événements | Métriques | Tier | Auto |
|----|---------|---------------|---------|-------------------|-------------------|------------|-----------|------|------|
| `import.apple.stream` | import | Bridge runtime, port import mocké | `import_playlist` stream 1 piste | `ImportResultState` phase=completed, track ADDED | session history JSON (si activé) | progress + diagnostic bridge | perf_span optionnel | integration | ✅ |
| `import.youtube.file` | import | Fichier JSON snapshot sur disque | `load_remote_playlist_from_file` | `RemotePlaylistSnapshot` parsé, `provider_id` défini | aucune jusqu'à `import_remote_playlist` | aucun | aucune | e2e | ✅ |
| `import.file.remote` | import | Repository tmp isolé | `import_remote_playlist` via bridge | `ManagedPlaylistDetail` origin=provider_library | `managed_playlists.json` + archive snapshot | aucun | aucune | e2e | ✅ |
| `import.apple.real` | import | macOS + Music.app + auth | Import Apple Music complet | Pistes dans bibliothèque | library + history | flux diagnostic complet | perf traces | e2e | ⏸ |

**Tests** : `test_import_stream_checkpoint_resume.py`, `test_ui_bridge_runtime.py`, `tests/e2e/test_user_journey_providers.py`, `test_youtube_music_gateway.py`

---

### Repository & snapshots

| ID | Domaine | Préconditions | Actions | Résultats attendus | Données persistées | Événements | Métriques | Tier | Auto |
|----|---------|---------------|---------|-------------------|-------------------|------------|-----------|------|------|
| `create.local.repository` | repository | Repository vide | import snapshot distant ou migration history | `local_playlist_id` assigné, version=1 | `managed_playlists.json` | aucun | aucune | e2e | ✅ |
| `snapshot.archive` | snapshots | Snapshot avec checksum | stocker 2× le même snapshot | un seul fichier dans snapshots/ | `data/snapshots/snap-<checksum>.json` | aucun | aucune | unit | ✅ |

**Tests** : `tests/e2e/test_user_journey_sync.py`, `test_playlist_repository.py`

---

### Synchronisation

| ID | Domaine | Préconditions | Actions | Résultats attendus | Données persistées | Événements | Métriques | Tier | Auto |
|----|---------|---------------|---------|-------------------|-------------------|------------|-----------|------|------|
| `sync.dry_run` | sync | Snapshots local + distant en params | `plan_sync` sync_mode=dry_run | plan d'actions, pas de mutation | `sync_operations.json` inchangé | `sync.plan.completed` | duration_ms, actions_total | e2e | ✅ |
| `sync.apply.append` | sync | checksum plan, versions alignées, write port | `apply_sync` push append_only | opération COMPLETED, playlist synced | `sync_operations.json`, `managed_playlists.json` | `sync.apply.started/completed` | compteurs succès | e2e | ✅ |
| `sync.partial_failure` | sync | Write port échoue au 2e appel | `apply_sync` avec port défaillant | opération PARTIAL ou FAILED | `sync_operations.json` avec failed_actions | `sync.apply.failed` ou completed avec actions_failed>0 | failure_counts | integration | ✅ |
| `sync.conflicts.resolve` | sync | Métadonnées local/distant conflictuelles | `plan_sync` manual_resolve puis `resolve_sync_conflicts` | nouveau `plan_checksum` après résolution | aucune jusqu'à apply | `sync.plan.completed` | conflicts_total dans event plan | e2e | ✅ |

**Tests** : `tests/e2e/test_user_journey_sync.py`, `test_resolve_sync_bridge.py`, `test_playlist_sync_conflicts.py`, `test_playlist_sync_apply.py`

---

### Historique & migration

| ID | Domaine | Préconditions | Actions | Résultats attendus | Données persistées | Événements | Métriques | Tier | Auto |
|----|---------|---------------|---------|-------------------|-------------------|------------|-----------|------|------|
| `history.migration` | history | Session history avec outcomes import | `list_managed_playlists` déclenche migration | playlist `hist-*` dans vue repository | `managed_playlists.json` au 1er list | aucun | aucune | e2e | ✅ |
| `migration.history_idempotent` | migration | Même session history listée 2× | `list_managed_playlists` ×2 | une seule playlist migrée | `managed_playlists.json` stable | aucun | aucune | unit | ✅ |

**Tests** : `tests/e2e/test_user_journey_history.py`, `test_playlist_library_bridge.py`, `test_playlist_repository.py`

---

### Observability & plugins

| ID | Domaine | Préconditions | Actions | Résultats attendus | Données persistées | Événements | Métriques | Tier | Auto |
|----|---------|---------------|---------|-------------------|-------------------|------------|-----------|------|------|
| `observability.diagnostics` | observability | Bus observability actif | `diagnostics` après plan sync | observability.health + metrics + sync_timeline | bus mémoire uniquement | `system.health_check` | event_count, average_duration_ms | e2e | ✅ |
| `plugins.extension_points` | plugins | Package platform chargé | snapshot diagnostics | extension_points + extension_api_version | aucune | aucun | aucune | e2e | ✅ |

**Tests** : `tests/e2e/test_user_journey_providers.py`, `test_observability_foundations.py`, `test_plugin_platform_foundations.py`

---

### Providers

| ID | Domaine | Préconditions | Actions | Résultats attendus | Données persistées | Événements | Métriques | Tier | Auto |
|----|---------|---------------|---------|-------------------|-------------------|------------|-----------|------|------|
| `providers.list` | providers | Apple + YouTube gateways enregistrés | `list_providers` | apple_music available, youtube experimental | aucune | aucun | aucune | e2e | ✅ |

**Tests** : `tests/e2e/test_user_journey_providers.py`, `test_multi_provider_readiness.py`

---

### Erreurs & reprise

| ID | Domaine | Préconditions | Actions | Résultats attendus | Données persistées | Événements | Métriques | Tier | Auto |
|----|---------|---------------|---------|-------------------|-------------------|------------|-----------|------|------|
| `errors.invalid_bridge` | errors | Bridge JSON-RPC | commande malformée ou params manquants | ok=false, BridgeErrorCode | aucune | diagnostic error optionnel | aucune | unit | ✅ |
| `resume.import.checkpoint` | resume | Checkpoint import mi-stream | reprendre import_stream depuis checkpoint | pistes restantes traitées | import session store | progress events | aucune | integration | ✅ |

**Tests** : `test_ui_bridge_parsing_errors.py`, `test_ui_bridge_json_rpc.py`, `test_import_stream_checkpoint_resume.py`, `test_manual_acquisition_resume.py`

---

### Génération (non E2E CI)

| ID | Domaine | Préconditions | Actions | Résultats attendus | Données persistées | Événements | Métriques | Tier | Auto |
|----|---------|---------------|---------|-------------------|-------------------|------------|-----------|------|------|
| `generation.catalog` | generation | Catalogue iTunes accessible ou mocké | `generate_playlist` via bridge | PlaylistGenerationResult avec sections | session history optionnelle | aucun | aucune | integration | ⏸ |

**Tests unitaires/intégration** : `test_generate_playlist.py`, `test_discovery_pipeline.py`, `test_generation_fulfillment.py`

---

## Commandes bridge — couverture fonctionnelle

27 commandes définies dans `BridgeCommand`. Couverture E2E actuelle :

| Commande | E2E | Integration | Unit |
|----------|-----|-------------|------|
| `list_providers` | ✅ | ✅ | ✅ |
| `load_remote_playlist_from_file` | ✅ | — | ✅ |
| `import_remote_playlist` | ✅ | — | ✅ |
| `list_managed_playlists` | ✅ | ✅ | ✅ |
| `plan_sync` | ✅ | ✅ | ✅ |
| `apply_sync` | ✅ | ✅ | ✅ |
| `resolve_sync_conflicts` | ✅ | ✅ | ✅ |
| `diagnostics` | ✅ | — | ✅ |
| `import_playlist` | — | ✅ | ✅ |
| `generate_playlist` | — | partiel | ✅ |
| `list_history` / `get_history_session` | — | — | ✅ |
| `continue_manual_acquisition` | — | ✅ | ✅ |
| `provider_auth_*` | — | — | ✅ |
| `autocomplete_search` | — | — | ✅ |

**Zones non couvertes en E2E** (priorité future) :
- `generate_playlist` bout-en-bout via bridge
- `provider_connect` / `provider_disconnect` avec auth réelle
- `list_remote_playlists` / `get_remote_playlist` avec provider live
- `retry_import_tracks` via bridge complet
- `replay_generation` / export history

## Exécution

```bash
# Suite complète (CI)
python -m pytest -q

# E2E uniquement
python -m pytest tests/e2e -q

# Par marqueur
python -m pytest -m e2e -q
python -m pytest -m integration -q

# Audit couverture fonctionnelle (scénarios → fichiers)
python -m pytest tests/e2e/test_functional_coverage.py -q
```

## Tests redondants — décision

| Fichier | Statut | Raison |
|---------|--------|--------|
| `test_e2e_import_mocked.py` | **Conservé**, marqué `integration` | Couvre import stream + delivery batch ; nom legacy trompeur mais non dupliqué du harness E2E |
| `test_resolve_sync_bridge.py` | **Conservé**, marqué `integration` | Tests conflict resolution détaillés ; complète le test E2E round-trip |
| `test_e2e_import_mocked.py` vs `tests/e2e/` | **Complémentaires** | Ancien = import acquisition ; nouveau = repository/sync/providers |

Aucun test supprimé : la redondance était nominale (préfixe `e2e_`), pas fonctionnelle.

## Ajouter un scénario E2E

1. Définir `UserScenario` dans `tests/e2e/scenarios.py`
2. Ajouter l'entrée dans `SCENARIO_IMPLEMENTATION` (`test_functional_coverage.py`)
3. Implémenter le test dans `tests/e2e/test_user_journey_*.py`
4. Marquer `@pytest.mark.e2e` ou `@pytest.mark.integration`
5. Vérifier : `python -m pytest tests/e2e/test_functional_coverage.py -q`

## Métriques de couverture fonctionnelle

| Métrique | Valeur (v1.0) |
|----------|---------------|
| Scénarios documentés | 17 |
| Scénarios automatisés | 15 (88 %) |
| Scénarios non automatisés | 2 (`import.apple.real`, `generation.catalog` bridge) |
| Tests E2E marqués | 7 |
| Tests dans `tests/e2e/` | 27 (inclut audit + paramétrés) |
| Suite totale | 558 collectés, 557 pass + 1 skip |

Voir `docs/TEST_COVERAGE_MAP.md` pour le mapping fichier par fichier.
