# Observability Architecture — Resonance

## Objectif

Rendre Resonance **observable** pour un utilisateur avancé : comprendre **ce qui se passe**, **pourquoi**, **combien de temps** cela prend, **quelles opérations** sont exécutées, **quels providers** répondent, **quelles opérations échouent**, et **quelles playlists** sont concernées.

Cette couche **complète** les mécanismes existants (`DiagnosticEvent`, `perf_span`, journaux stderr, rapports d'import) — elle ne les remplace pas.

## Besoins utilisateur avancé

| Besoin | Mécanisme |
|--------|-----------|
| Ce qui se passe | Événements métier typés (`ResonanceEvent`) |
| Pourquoi | `message`, `attributes`, corrélation (`correlation_id`) |
| Durée | `duration_ms` sur plan/apply, métriques agrégées |
| Opérations exécutées | Journal `PlaylistSyncOperation` + événements `sync.apply.*` |
| Providers impliqués | `provider_id` sur chaque événement sync |
| Échecs | `success=False`, `sync.apply.failed`, compteurs métriques |
| Playlists concernées | `local_playlist_id` indexable dans le bus |

## Principes

1. **Découplage providers** — le package `playlist_builder/observability/` n'importe pas `integration.*`.
2. **Événements fortement typés** — `ResonanceEventKind` + `EventCategory`, pas de chaînes libres.
3. **Bus in-process** — rétention bornée, thread-safe, consommable par UI, tests, API future.
4. **Additive** — les logs stderr / bridge diagnostics restent la source opérationnelle immédiate.
5. **Exportable** — `export_observability_bundle()` pour diagnostics, CI, cloud futur.

## Composants (v1.0.0)

```
playlist_builder/observability/
├── api_version.py      # OBSERVABILITY_API_VERSION
├── events.py           # ResonanceEvent, ResonanceEventKind, EventCategory
├── bus.py              # ObservabilityBus, get_default_bus()
├── metrics.py          # MetricsCollector (compteurs, durées moyennes)
├── recorder.py         # ObservabilityRecorder, NoOpObservabilityRecorder
├── health.py           # build_health_report()
└── export.py           # export_observability_bundle()
```

### API d'événements interne

```python
from playlist_builder.observability import (
    ObservabilityBus,
    ObservabilityRecorder,
    ResonanceEvent,
    ResonanceEventKind,
    get_default_bus,
)

bus = get_default_bus()
recorder = ObservabilityRecorder(bus=bus)
recorder.record_sync_plan_completed(...)
bus.recent_events(category=EventCategory.SYNC, local_playlist_id="mpl-1")
```

### Événements v1

| Kind | Catégorie | Émis par (fondations) |
|------|-----------|------------------------|
| `sync.plan.completed` | SYNC | `plan_sync()` |
| `sync.apply.started` | SYNC | `ApplySyncPlaylist` |
| `sync.apply.completed` | SYNC | `ApplySyncPlaylist` |
| `sync.apply.failed` | SYNC | `ApplySyncPlaylist` |
| `sync.apply.blocked` | SYNC | `ApplySyncPlaylist` |
| `system.health_check` | SYSTEM | `build_diagnostics_snapshot()` |
| *(réservés)* | REPO/SNAPSHOT/PROVIDER/IMPORT/GENERATION | phases ultérieures |

### Intégrations actuelles

- **`ApplySyncPlaylist`** — émet started/completed/failed/blocked/no_op via `ObservabilityRecorder` (désactivable via `NoOpObservabilityRecorder`).
- **`plan_sync()`** — émet `sync.plan.completed` avec durée et totaux actions/conflits.
- **`build_diagnostics_snapshot()`** — expose `summary["observability"]` (health, metrics, sync_timeline, event_count).

### Health check

`build_health_report()` agrège :

- moteur Python reachable ;
- providers enregistrés / disponibles / connectés ;
- bus observabilité actif (`event_count`, `api_version`).

Statuts : `ok`, `degraded`, `unhealthy`.

### Export diagnostics

```python
from playlist_builder.observability import export_observability_bundle, build_health_report

bundle = export_observability_bundle(health=build_health_report(context, providers=providers))
# → api_version, health, metrics, recent_events, sync_timeline, sync_operations
```

## Consommateurs futurs

| Consommateur | Usage |
|--------------|-------|
| UI graphique | timeline sync, health badge, export |
| Outils diagnostic | bundle JSON complet |
| Tests | `reset_default_bus()`, assertions sur événements |
| API / cloud | sérialisation `to_dict()` stable versionnée |

## Hors scope (fondations)

- Persistance disque des événements (le journal `PlaylistSyncOperation` reste SSOT audit sync).
- OpenTelemetry / Prometheus (extension possible via adaptateur bus).
- Remplacement des `DiagnosticEvent` bridge ou `perf_span`.
- Émission provider-level (`provider.call`) — réservé quand un hook gateway neutre existera.

## Références

- [ADR-021](architecture/ADR-021-observability-layer.md)
- [ADR-006](architecture/ADR-006-observable-resolution-pipeline.md) — diagnostics résolution (provider-local, complémentaire)
