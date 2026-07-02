# Phase 4.7 — Laboratoire / Diagnostics

## Objectif

Premier écran **Laboratoire** dans Resonance macOS : diagnostics provider-neutral du moteur Python via l’Engine Bridge JSON-lines.

## Portée livrée

| Composant | Statut |
|-----------|--------|
| Commande bridge `diagnostics` enrichie | ✅ |
| Snapshot cache / providers / rapports récents | ✅ |
| `DiagnosticsView` dans la sidebar | ✅ |
| `DiagnosticsViewModel` (états + modes) | ✅ |
| `DiagnosticModels.swift` + `BridgeError.swift` | ✅ |
| Tests Python + Swift | ✅ |
| Historique des sessions | 📋 reporté (placeholder conservé) |

## Flux

```text
DiagnosticsView
  → DiagnosticsViewModel.refresh()
  → PythonEngineBridgeService.fetchDiagnostics()
  → BridgeClient (process Python one-shot)
  → diagnostics command
  → RuntimeEngineBridgeBackend.diagnostics()
  → DiagnosticsSnapshot (provider-neutral)
```

## Contenu du snapshot

Le résultat `diagnostics` expose :

- `engine_version` — version du package Python
- `summary` — objet structuré :
  - `bridge_status` (`connected`)
  - `platform`
  - `execution_ms`
  - `catalog_cache_entries` / `identity_cache_entries`
  - `active_providers` (disponibilité, connexion)
  - `recent_reports` — résumés des fichiers `reports/import_diagnostics_*.json` (sans `persistent_id`)
  - `reports_directory`
- `events` — timeline `DiagnosticEvent` (bridge, cache, providers, rapports)

## Modes d’affichage

| Mode | Contenu |
|------|---------|
| **Simple** | Résumé, providers, rapports récents, timeline sans événements `debug` |
| **Architecte** | Payload des événements, détails cache, compteurs bruts |

## États UI (`DiagnosticsViewModel`)

| État | Signification |
|------|----------------|
| `disconnected` | Initial |
| `running` | Refresh en cours |
| `connected` / `completed` | Snapshot chargé |
| `failed` | Erreur bridge typée (message utilisateur, pas de stack trace) |

## Contraintes respectées

- Aucun AppleScript / MusicKit / `persistent_id` dans SwiftUI
- Aucun import provider-specific côté écran Laboratoire
- Services injectables (`DiagnosticsServing`, mock pour tests)
- CLI inchangée

## Fichiers clés

### Python

- `playlist_builder/app/bridge_runtime/diagnostics_snapshot.py`
- `playlist_builder/app/bridge_runtime/backend.py` — `diagnostics()`
- `playlist_builder/ui/bridge/commands.py` — `DiagnosticsResult.summary`

### Swift

- `ResonanceCore/DiagnosticModels.swift`
- `ResonanceCore/BridgeError.swift`
- `ResonanceMac/Services/PythonEngineBridgeService.swift` — `DiagnosticsServing`
- `ResonanceMac/ViewModels/DiagnosticsViewModel.swift`
- `ResonanceMac/Screens/DiagnosticsView.swift`

## Tests

```bash
python -m pytest tests/test_ui_bridge_runtime.py -q
cd apps/resonance && ./scripts/build.sh
```

## Reporté (hors 4.7)

- Historique des sessions (sidebar placeholder conservé)
- Export JSON / ouverture dossier reports depuis l’UI
- Streaming live des événements pendant génération/import
- Filtres session/provider/date avancés

## Prochaines étapes

- **4.8** — Historique sessions + persistance locale
- Relier le Laboratoire aux événements live du bridge pendant import
- Export diagnostics depuis l’UI

## macOS usability fixes (4.8a)

- Diagnostics parsing tolerates minimal bridge payloads (missing `summary` defaults).
- User-facing errors distinguish bridge unavailable vs invalid response; architect mode shows technical detail.
- `ResonancePaths` resolves repo root from executable path when cwd is `.build/`.
