# Architecture technique

*Comment c'est construit — moteur Python, gateway providers, interface Resonance.*

## Vue d'ensemble (2026)

```
┌─────────────────────────────────────────────────────────────────┐
│                    POINTS D'ENTRÉE                               │
│  CLI (check_catalog, generate, create)   apps/resonance (macOS) │
└────────────┬───────────────────────────────┬──────────────────────┘
             │                               │
┌────────────▼──────────────┐   ┌───────────▼────────────────────┐
│  playlist_builder/cli/     │   │  cli/engine_bridge.py (4.6)   │
│  + app/use_cases/          │   │  + app/bridge_runtime/        │
└────────────┬──────────────┘   └───────────┬────────────────────┘
             │                               │
┌────────────▼───────────────────────────────▼────────────────────┐
│  ui/bridge/  (JSON-lines, provider-neutral)                       │
│  ui/shared/  — DTO, validation, thèmes                            │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│                    COUCHE APPLICATION                            │
│  app/use_cases/  ·  app/factory.py  ·  session/                 │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│                    INTÉGRATION GATEWAY                           │
│  integration/gateway/  — registre providers neutre               │
│  integration/apple_music/  — Apple Music (isolé)                 │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│                    MOTEUR MÉTIER                               │
│  canonical/  ·  discovery/  ·  planning/  ·  generation/      │
│  scoring/  ·  resolver/  ·  playlists/  ·  catalog/             │
└────────────┬────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│                    CORE + INFRASTRUCTURE                         │
│  core/  ·  infrastructure/cache/  ·  reports/                 │
└─────────────────────────────────────────────────────────────────┘
```

## Package `playlist_builder`

### Couche canonique & métier

| Module | Rôle |
|--------|------|
| `canonical/` | Modèles neutres, `ProviderId`, identités morceaux |
| `discovery/` | Pipeline découverte candidats |
| `planning/` | Planification avec contraintes (énergie, exclusions) |
| `generation/` | Générateur déterministe |
| `scoring/` | Moteur de scoring et contraintes |
| `playlists/` | Chargement et export JSON |

### Intégration (Phases 2–3)

| Module | Rôle |
|--------|------|
| `integration/gateway/` | `ProviderGatewayRegistry` — point d'entrée neutre |
| `integration/apple_music/` | Gateway Apple Music, import, acquisition catalogue |
| `app/use_cases/` | `ImportPlaylistUseCase`, `CheckCatalogUseCase` |
| `app/factory.py` | Composition des dépendances |

**Règle :** `ui/` n'importe **jamais** `integration/apple_music/` directement.

### Couche UI (Phase 4)

| Module | Rôle |
|--------|------|
| `ui/shared/dto/` | Contrats : `PlaylistGenerationRequest`, `ProviderOption`… |
| `ui/shared/validation/` | Validateurs purs (Phase 4.1) |
| `ui/shared/navigation/` | `AppRoute` |
| `ui/shared/theme/` | `ThemeRegistry`, `ThemeManager`, `.theme.json` |
| `ui/bridge/` | JSON-lines : commands, errors, json_rpc |
| `app/bridge_runtime/` | Runtime moteur ↔ bridge (Phase 4.6) |
| `cli/engine_bridge.py` | Point d'entrée stdin/stdout pour Resonance |

→ [Phase 4 — Interface Resonance](Phase-4-Interface-Resonance)

### App macOS `apps/resonance/`

| Target Swift | Rôle |
|--------------|------|
| `ResonanceCore` | Miroir DTO + validation + contrats bridge |
| `ResonanceDesign` | `ThemeManager`, tokens JSON |
| `ResonanceMac` | Shell SwiftUI (sidebar, Accueil, Paramètres, Builder) |

```bash
cd apps/resonance && ./scripts/build.sh && swift run ResonanceMac
```

## Moteur Apple Music (intégration)

Le workflow CLI macOS utilise `integration/apple_music/` :

- Résolution identité → bibliothèque → acquisition catalogue si absent
- Livraison playlist via AppleScript (moteur principal)
- MusicKit expérimental en option

L'**UI Resonance** n'embarque pas AppleScript — elle passera par le **Engine Bridge**.

## Phase 2 — Planning & Generation

```python
PlaylistPlanner.plan(request, candidates)
PlaylistGenerator.build(request, candidates)
```

Profils d'énergie : `chill`, `steady`, `rising`, `party`, `max_from_start`, `random`.

→ [Phase 2 — Génération](Phase-2-Generation)

## Dépendances

**Runtime :** Python 3.12+ stdlib (moteur).  
**Dev :** `pytest>=8.0`.  
**macOS UI :** Swift 5.9+, Xcode toolchain.

## Tests

```bash
python3 -m pytest -q                    # tout le repo (~270 tests)
cd apps/resonance && ./scripts/build.sh  # Swift (macOS)
```

Couverture :
- Scoring, validation JSON, cache, planning, génération
- Gateway Apple Music E2E
- Contrats UI (`test_ui_shared_*`, `test_ui_bridge_*`, `test_ui_shared_theme`)
- Guards : pas d'import provider dans `ui/`
- Shell macOS (`test_resonance_mac_shell`)

## Fichiers générés (gitignored)

| Dossier | Contenu |
|---------|---------|
| `reports/` | CSV, HTML, TXT, diagnostics import |
| `cache/` | Cache API et identités |
| `apps/resonance/.build/` | Artefacts Swift |

## Analogies Guidewire

| Concept | Équivalent Guidewire |
|---------|----------------------|
| `canonical/` + gateway | Product model + integration gateway |
| `ui/shared` DTO | PCF / contrats de données |
| Engine Bridge | API REST interne ClaimCenter |
| `ThemeRegistry` | Thèmes PolicyCenter |
| JSON playlist | Spécification produit |

---

*Architecture en couches, providers isolés, UI provider-neutral. Comme un bon delivery enterprise — mais avec plus de Daft Punk.*
