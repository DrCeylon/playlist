# Phase 4.6 — Import UX + Python engine bridge runtime

Connects Resonance macOS to the Python engine: real generation preview, Apple Music import flow, and user-facing progress/report screens.

## User flow

```text
Nouvelle Playlist (form)
  → Générer
  → Preview (moteur Python ou fallback mock)
  → Importer dans Apple Music
  → ImportProgressView (résolution / cache / catalogue)
  → [optional] acquisition manuelle Music.app
  → ImportReportView (rapport laboratoire)
```

## Scope delivered (4.6)

| Area | Status | Notes |
|------|--------|-------|
| Génération réelle via bridge | ✅ | `generate_playlist` → `GenerationSessionEngine` |
| Preview depuis Python | ✅ | `PlaylistGenerationResult` affiché dans `PlaylistPreviewView` |
| Bouton import | ✅ | Depuis la preview |
| Progression import | ✅ | `ImportProgressView` — phases, diagnostics |
| Rapport final | ✅ | `ImportReportView` — ajoutés / ignorés / introuvables / erreurs |
| Acquisition manuelle | ✅ UX, ⚠️ limitation | Pause + `continue_manual_acquisition` ; voir § Limitations |
| Fallback mock | ✅ | Si process Python indisponible (dev/tests hors macOS) |
| Provider-specific en Swift | ❌ interdit | Respecté — tout passe par le bridge |

## Known limitations (4.6 vs 4.6b)

Documentées explicitement pour les critères d'acceptation :

| Limitation | Impact utilisateur | Plan 4.6b |
|------------|-------------------|-------------|
| **Un process Python par commande** | Génération et import lancent `python3 -m playlist_builder.cli.engine_bridge` à chaque action | Process bridge persistant (stdin/stdout ouvert) |
| **Événements import en fin de process** | La barre de progression saute plutôt que de défiler en temps réel | Streaming live pendant l'exécution |
| **Import sync uniquement** | Pas d'import incrémental `sync=false` depuis l'UI | Paramètre UI + bridge |
| **Import macOS only** | `provider_unavailable` hors macOS | Normal — Apple Music delivery |
| **Acquisition manuelle** | Music.app ouverte par Python ; reprise via nouvelle commande bridge + session fichier | Process persistant pour reprise instantanée |

L'import est **fonctionnel sur macOS** avec Music.app et le moteur configuré. Hors macOS ou sans Python, l'UX import existe mais retourne une erreur claire (`bridgeUnavailable` / `provider_unavailable`).

## Architecture

```text
ResonanceMac (SwiftUI)
  PythonEngineBridgeService
    → BridgeClient (JSON-lines, one-shot process)
    → python3 -m playlist_builder.cli.engine_bridge

playlist_builder/app/bridge_runtime/   ← composition root (hors ui/bridge)
  RuntimeEngineBridgeBackend
    generate → GenerationSessionEngine
    import   → stream_import_playlist → AppleMusicResolver + Delivery

playlist_builder/ui/bridge/            ← contrat provider-neutral
  JsonRpcEngineBridge, commands, events, errors
```

**Règle :** `ui/bridge/` n'importe pas les providers. Le runtime vit dans `app/bridge_runtime/`.

## Bridge commands (4.6)

| Command | Rôle |
|---------|------|
| `generate_playlist` | Validation + génération → `generation` payload |
| `import_playlist` | Import streamé → événements + `import` payload |
| `continue_manual_acquisition` | Reprend une session (`import_session_id`) |
| `validate_generation_request` | Validation seule (tests/outils) |
| `list_providers` | Statut providers (Apple Music indisponible hors macOS) |
| `diagnostics` | Version moteur |

### Événements import

| Événement | Payload typique |
|-----------|-----------------|
| `started` | `command` |
| `progress` | `phase`, `processed_tracks`, `total_tracks`, `current_track_label` |
| `diagnostic` | `phase` (`cache_hit`, `catalog_lookup`, …), `message` |
| `manual_acquisition_required` | `import_session_id`, `token`, `artist`, `title`, `instructions` |
| `completed` | résumé import |

### Codes d'erreur

`invalid_request`, `validation_failed`, `engine_error`, `provider_unavailable`, `manual_action_required`, `not_configured`

**Jamais exposé à l'UI :** `persistent_id`, AppleScript, clés provider internes.

## Swift modules

| Fichier | Rôle |
|---------|------|
| `ResonanceCore/BridgeClient.swift` | Process Python, encode/decode JSON-lines |
| `ResonanceCore/BridgeCommand.swift` | Enum commandes |
| `ResonanceCore/BridgeResponse.swift` | Parse responses / events |
| `ResonanceCore/ImportModels.swift` | `ImportPhase`, `ImportTrackStatus`, `ImportResultState` |
| `ResonanceMac/PythonEngineBridgeService.swift` | Génération + import injectables |
| `ResonanceMac/MockPlaylistImportService.swift` | Tests / dev sans moteur |
| `ResonanceMac/ImportViewModel.swift` | États import + acquisition manuelle |
| `ResonanceMac/ImportProgressView.swift` | Progression + prompt manuel |
| `ResonanceMac/ImportReportView.swift` | Rapport final style laboratoire |

## Manual acquisition flow

1. Python détecte un morceau catalogue absent de la bibliothèque.
2. Music.app peut être ouverte par le moteur (côté Python uniquement).
3. Bridge émet `manual_acquisition_required` + sauvegarde `ImportSessionCheckpoint`.
4. UI affiche instructions + bouton **« J'ai ajouté le morceau, continuer »**.
5. Swift envoie `continue_manual_acquisition` avec `import_session_id`.
6. Moteur reprend la résolution ; `IdentityCache` rempli si succès.

## Configuration

| Variable | Usage |
|----------|-------|
| `RESONANCE_REPO_ROOT` | Racine du repo si auto-détection échoue |
| CWD | `BridgeClient` utilise la racine contenant `playlist_builder/` |

```bash
# Lancer le bridge manuellement (debug)
cd /chemin/vers/playlist
python3 -m playlist_builder.cli.engine_bridge
```

## Tests

| Layer | Fichiers |
|-------|----------|
| Python runtime | `tests/test_ui_bridge_runtime.py` |
| Python bridge | `tests/test_ui_bridge_json_rpc.py`, `test_ui_bridge_guard.py` |
| Swift bridge | `BridgeClientTests.swift` |
| Swift import VM | `ImportViewModelTests.swift` |
| Contrat cross-lang | `tests/test_resonance_playlist_builder.py` |

```bash
python3 -m pytest -q
cd apps/resonance && ./scripts/build.sh   # macOS
```

## Acceptance criteria (4.6)

- [x] App macOS se lance (`swift run ResonanceMac`)
- [x] Nouvelle Playlist appelle le moteur réel (ou fallback mock documenté)
- [x] Preview réelle depuis Python quand bridge disponible
- [x] Bouton import présent sur la preview
- [x] Import fonctionnel macOS + UX complète avec limitations documentées
- [x] Aucun provider-specific dans Swift
- [x] CLI inchangée et pytest vert
- [x] PR focalisée Phase 4.6

## Related

- [phase-4-6-bridge-runtime.md](phase-4-6-bridge-runtime.md) — notes techniques runtime
- [phase-4-playlist-builder.md](phase-4-playlist-builder.md) — formulaire 4.5
- [phase-4-engine-bridge.md](phase-4-engine-bridge.md) — protocole JSON-lines 4.2
- [../architecture/phase-4-ui-architecture.md](../architecture/phase-4-ui-architecture.md)

## Next (4.7)

- Historique des sessions
- Écran Laboratoire (diagnostics stream)
- Process bridge persistant (4.6b)
