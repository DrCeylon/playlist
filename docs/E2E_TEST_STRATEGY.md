# Stratégie de tests End-to-End — Resonance v1.0

Ce document définit la stratégie de tests d'intégration et End-to-End (E2E) pour Resonance. Il complète la couverture unitaire en vérifiant que les briques fonctionnent **ensemble** via le pont JSON-RPC (`JsonRpcEngineBridge` → `RuntimeEngineBridgeBackend`).

## Objectifs

| Objectif | Approche |
|----------|----------|
| Déterminisme | Harness isolé (`tmp_path`), fakes injectés, pas de réseau ni Music.app |
| Reproductibilité | Checksums et timestamps fixes, `reset_default_bus()` par harness |
| Indépendance | Fixture `e2e_harness` — aucun état global partagé |
| Rapidité | `tests/e2e/` : **35 tests en ~0,1 s** ; suite Python ~2 min |
| CI | `python -m pytest -q` sur Ubuntu ; Apple réel réservé à `resonance-macos.yml` |

## Pyramide (honest tiering)

```
                    ┌──────────────────┐
                    │  E2E (2 marqués) │  Parcours transversal bridge → persistance
                    ├──────────────────┤
                    │ Integration (13+) │  Bridge + multi-modules + fakes
                    ├──────────────────┤
                    │  Unit (~560)      │  Modules isolés
                    └──────────────────┘
```

### Définitions strictes

| Niveau | Critère | Exemple |
|--------|---------|---------|
| **E2E** | JSON-RPC → backend → use cases → repository → adapter fake, **sans raccourci setup** significatif | `test_e2e_sync_dry_run_then_apply_append` |
| **Intégration** | Plusieurs modules via bridge ou harness, setup partiel ou commande unique | `test_integration_bridge_sync.py`, `test_resolve_sync_bridge.py` |
| **Audit / meta** | Registre scénarios, pas de parcours produit | `test_functional_coverage.py` |
| **Unitaire** | Module isolé | `test_playlist_sync_planning.py` |

Le marqueur `@pytest.mark.e2e` est **réservé** aux 2 parcours transversaux. Les tests utiles du dossier `tests/e2e/` peuvent être `integration`.

## Harness (`tests/e2e/harness.py`)

### Isolation complète (sous `tmp_path`)

| Chemin | Rôle |
|--------|------|
| `data/managed_playlists.json` | SSOT playlists |
| `data/snapshots/` | Archives immuables |
| `data/sync_operations.json` | Journal sync |
| `data/provider_auth/` | Auth providers (vide en tests) |
| `data/history/sessions.json` | History isolée (override backend) |
| `cache/catalog.json`, `cache/identity.json` | Caches désactivés |

### Mocks documentés

| Composant | Mock | Non mocké |
|-----------|------|-----------|
| Apple Music sync | `FakeSyncGateway` + `FakeWritePort` | — |
| YouTube | Gateway enregistré (metadata `list_providers` uniquement) | Pas d'appel API |
| Music.app / réseau | Absent | — |
| Observability | Bus réinitialisé | Émission sync réelle |

### Déterminisme

- Pas de `sleep`, pas de UUID aléatoires dans les assertions
- `sample_remote_playlist_dict(checksum=...)` — checksums explicites
- Timestamps ISO fixes dans les fixtures

## Classification des 35 tests dans `tests/e2e/`

| Classe | Nombre | Fichiers |
|--------|--------|----------|
| **Vrai E2E** | 2 | `test_user_journey_sync.py` |
| **Intégration bridge** | 10 | `test_integration_bridge_sync.py`, `test_user_journey_providers.py`, `test_user_journey_history.py` |
| **Audit / meta** | 23 | `test_functional_coverage.py` (1 + 19 paramétrés + 3 smoke) |

### Vrais E2E (2)

1. `test_e2e_import_remote_repository_plan_sync` — import → snapshot → plan_sync dry_run
2. `test_e2e_sync_dry_run_then_apply_append` — import → plan → apply → journal + observability

### Intégration bridge (10)

- Idempotence apply, plan obsolète, version locale obsolète, mirror bloqué
- Échec partiel + journal, résolution conflits
- list_providers, load fichier, diagnostics sans secrets, migration history

## Scénarios (`tests/e2e/scenarios.py`)

- **22 scénarios** documentés, **20 automatisés**
- Tiers alignés sur les marqueurs pytest réels
- Non automatisés : `generation.catalog`, `import.apple.real` (macOS)

## Scénarios prioritaires couverts

| Scénario | Tier | Test |
|----------|------|------|
| import → repository → plan_sync | e2e | `test_e2e_import_remote_repository_plan_sync` |
| apply append_only + observability | e2e | `test_e2e_sync_dry_run_then_apply_append` |
| apply idempotent | integration | `test_integration_apply_sync_idempotent_via_bridge` |
| plan obsolète | integration | `test_integration_stale_plan_checksum_rejected_via_bridge` |
| version locale obsolète | integration | `test_integration_stale_local_version_rejected_via_bridge` |
| mirror sans confirmation | integration | `test_integration_mirror_blocked_without_confirmation_via_bridge` |
| apply partiel + journal | integration | `test_integration_partial_sync_write_failure_records_operation` |
| migration history idempotente | integration | `test_integration_history_migration_via_list_managed_playlists` |
| diagnostics sans secrets | integration | `test_integration_diagnostics_observability_no_secret_leak` |

## Gaps honnêtes (non simulés)

- `generate_playlist` via bridge E2E
- YouTube write / sync production
- mirror/reorder apply réel (Music.app)
- `list_remote_playlists` avec bibliothèque live
- Import Apple Music réel (workflow macOS)

## Exécution

```bash
python3.12 -m pytest tests/e2e -q              # Dossier harness (35 tests)
python3.12 -m pytest -m e2e -q                 # 2 vrais E2E uniquement
python3.12 -m pytest -m integration -q        # Intégration (13+ global)
python3.12 -m pytest -q                       # Suite complète CI
```

## `pyproject.toml`

- `pythonpath = ["."]` — permet `from tests.e2e...` sans casser la découverte
- Marqueurs déclarés ; tests sans marqueur restent **unitaires par défaut**
- Aucun filtre implicite sur `testpaths`

## Métriques (juillet 2026, post-#78)

| Métrique | Valeur |
|----------|--------|
| Suite Python | 574 pass + 1 skip |
| `tests/e2e/` | 35 tests, ~0,1 s |
| Marqués `e2e` | 2 |
| Marqués `integration` (global) | 13 |
| Scénarios documentés | 22 |
| Scénarios automatisés | 20 (91 %) |

Voir `docs/TEST_COVERAGE_MAP.md` pour le mapping fichier par fichier.
