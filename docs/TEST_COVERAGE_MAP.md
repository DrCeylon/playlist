# Cartographie de couverture des tests — Resonance v1.0

Ce document distingue **couverture unitaire**, **intégration** et **End-to-End** pour chaque fichier de test. Il sert de rapport de couverture fonctionnelle (pas de couverture de lignes de code).

Dernière mise à jour : suite `558` tests collectés, `557` pass + `1` skip.

## Synthèse

| Niveau | Fichiers | Tests (~) | Rôle |
|--------|----------|-----------|------|
| **E2E** | 4 (+ audit) | 7 marqués + 20 audit/harness | Parcours utilisateur via bridge JSON-RPC |
| **Intégration** | ~12 | ~40+ | Multi-modules, fakes, mocks réseau |
| **Unitaire** | ~70 | ~510 | Logique isolée, DTO, planning, scoring |

## Tests E2E (`tests/e2e/`)

| Fichier | Scénarios couverts | Marqueur |
|---------|-------------------|----------|
| `harness.py` | Infrastructure (non test) | — |
| `scenarios.py` | Registre des 17 scénarios | — |
| `conftest.py` | Fixture `e2e_harness` | — |
| `test_user_journey_sync.py` | import.file.remote, create.local.repository, sync.dry_run, sync.apply.append, sync.partial_failure, sync.conflicts.resolve | e2e / integration |
| `test_user_journey_providers.py` | providers.list, import.youtube.file, observability.diagnostics, plugins.extension_points | e2e |
| `test_user_journey_history.py` | history.migration, migration.history_idempotent | e2e |
| `test_functional_coverage.py` | Audit scénario→fichier, détection orphelins | — |

## Tests d'intégration (hors `tests/e2e/`)

| Fichier | Domaine | Scénarios / focus |
|---------|---------|-------------------|
| `test_e2e_import_mocked.py` | import | import.apple.stream (nom legacy, tier integration) |
| `test_resolve_sync_bridge.py` | sync | sync.conflicts.resolve (détail bridge) |
| `test_integration_gateway.py` | providers | Registry + gateway multi-provider |
| `test_integration_apple_music.py` | import Apple | Flux Apple mocké bout-en-bout |
| `test_import_stream_checkpoint_resume.py` | resume | resume.import.checkpoint |
| `test_manual_acquisition_resume.py` | resume | Reprise acquisition manuelle |
| `test_manual_acquisition_continue_button.py` | acquisition | Continue manual acquisition |
| `test_manual_acquisition_history_resume.py` | history | Reprise depuis history |
| `test_playlist_library_bridge.py` | repository | list_managed_playlists, migration |
| `test_playlist_sync_bridge.py` | sync | Commands sync via bridge |
| `test_remote_playlist_bridge.py` | import | Remote playlist commands |
| `test_ui_bridge_runtime.py` | bridge | Runtime backend intégré |

## Tests unitaires par domaine

### Bridge & UI

| Fichier | Focus |
|---------|-------|
| `test_ui_bridge_json_rpc.py` | Protocole JSON-RPC, errors.invalid_bridge |
| `test_ui_bridge_commands.py` | Parsing commandes |
| `test_ui_bridge_parsing_errors.py` | Erreurs malformed |
| `test_ui_bridge_guard.py` | Guards validation |
| `test_bridge_command_contract.py` | Contrat 27 commandes |
| `test_ui_shared_dto.py` | DTO partagés |
| `test_ui_shared_validation.py` | Validation DTO |
| `test_ui_shared_guard.py` | Guards DTO |
| `test_ui_shared_theme.py` | Thèmes UI |
| `test_ui_history.py` | History DTO/commands |
| `test_autocomplete_bridge.py` | Autocomplete |
| `test_resonance_mac_shell.py` | Shell macOS (structure) |

### Sync & repository

| Fichier | Focus |
|---------|-------|
| `test_playlist_sync_planning.py` | Algorithme plan sync |
| `test_playlist_sync_apply.py` | Application actions sync |
| `test_playlist_sync_conflicts.py` | Détection/résolution conflits |
| `test_playlist_sync_operations.py` | Persistance opérations |
| `test_playlist_repository.py` | Repository + snapshot.archive |
| `test_sync_architecture.py` | Architecture sync |
| `test_remote_playlist_dto.py` | DTO remote playlist |

### Providers & plateforme

| Fichier | Focus |
|---------|-------|
| `test_multi_provider_readiness.py` | Multi-provider readiness |
| `test_provider_platform_ports.py` | Ports plateforme |
| `test_provider_import_port.py` | Port import provider |
| `test_youtube_music_gateway.py` | Gateway YouTube |
| `test_youtube_architecture.py` | Architecture YouTube |
| `test_plugin_platform_foundations.py` | Plugins extension points |
| `test_observability_foundations.py` | Bus events/metrics |

### Apple Music

| Fichier | Focus |
|---------|-------|
| `test_apple_music_playlist_read.py` | Lecture playlists |
| `test_apple_music_playlist_write.py` | Écriture playlists |
| `test_apple_music_resolver.py` | Résolution catalog |
| `test_apple_music_delivery.py` | Livraison tracks |
| `test_apple_music_delivery_pacing.py` | Pacing delivery |
| `test_apple_music_catalog_ids.py` | IDs catalog |
| `test_apple_music_catalog_fallback.py` | Fallback catalog |
| `test_apple_music_mapper_resolution.py` | Mapping résolution |
| `test_apple_music_acquire_instrumentation.py` | Instrumentation acquire |
| `test_apple_music_acquire_script.py` | Script acquire |
| `test_apple_music_manual_acquisition.py` | Acquisition manuelle |
| `test_apple_music_library_acquisition.py` | Acquisition library |
| `test_musickit_client.py` | Client MusicKit |

### Acquisition & import

| Fichier | Focus |
|---------|-------|
| `test_manual_acquisition_workflow_architecture.py` | Workflow architecture |
| `test_manual_acquisition_perf_span.py` | Perf spans |
| `test_manual_continue_trace.py` | Continue trace |
| `test_acquisition_strategy_experiments.py` | Stratégies acquisition |
| `test_acquisition_production_policy.py` | Policy production |
| `test_retry_import_existing_outcomes.py` | Retry import |
| `test_app_import_playlist.py` | App import |

### Génération & scoring

| Fichier | Focus |
|---------|-------|
| `test_generate_playlist.py` | CLI generate |
| `test_generation_fulfillment.py` | Fulfillment génération |
| `test_discovery_pipeline.py` | Pipeline discovery |
| `test_scoring.py` | Moteur scoring |
| `test_resolver.py` | Resolver |
| `test_keyword_suggestion.py` | Suggestions mots-clés |
| `test_planning.py` | Planning |
| `test_sprint2_planning.py` | Sprint 2 planning |

### Core & infrastructure

| Fichier | Focus |
|---------|-------|
| `test_canonical.py` | Modèles canoniques |
| `test_core.py` | Core models |
| `test_cache.py` | Cache |
| `test_identity_cache.py` | Identity cache |
| `test_atomic_json.py` | Persistance JSON atomique |
| `test_music_client.py` | Music client |
| `test_itunes_multi_search.py` | Recherche iTunes |
| `test_perf_trace.py` | Perf tracing |
| `test_retry_policy.py` | Retry policy |
| `test_check_environment.py` | Environment check |
| `test_cli_create_playlist_flags.py` | CLI flags |

### Release & docs

| Fichier | Focus |
|---------|-------|
| `test_release_readiness.py` | Release readiness |
| `test_product_vision_docs.py` | Docs vision produit |
| `test_resonance_playlist_builder.py` | Package structure |
| `test_app_icon_assets.py` | Assets icône |

## Zones non testées (gaps)

| Zone | Risque | Action recommandée |
|------|--------|-------------------|
| `generate_playlist` via bridge E2E | Moyen | Ajouter test harness avec catalog mocké |
| `provider_connect` auth réelle | Faible (UI) | Workflow macOS manuel ou mock OAuth |
| `list_remote_playlists` live | Moyen | Fake gateway avec bibliothèque fixture |
| `retry_import_tracks` bridge E2E | Moyen | Étendre harness import |
| Import Apple Music réel | Élevé prod | `resonance-macos.yml` workflow |
| Conflits sync destructive (replace) | Moyen | Scénario apply replace_only |
| Migration données legacy v0→v1 | Faible | Test fixture ancien format JSON |

## Commandes pytest par tier

```bash
# Unitaires implicites (tout sauf marqués)
python -m pytest -q -m "not integration and not e2e"

# Intégration
python -m pytest -q -m integration

# E2E
python -m pytest -q -m e2e

# Dossier E2E complet (inclut audit)
python -m pytest tests/e2e -q
```

## Évolution

Pour maintenir la cartographie à jour :
1. Nouveau scénario → `scenarios.py` + `SCENARIO_IMPLEMENTATION`
2. Nouveau fichier test → ajouter une ligne dans ce document
3. CI : la suite complète `python -m pytest -q` reste la gate unique
