# Phase 4 — Interface Resonance

*De la CLI au shell macOS SwiftUI — architecture produit cross-platform.*

→ Détails techniques : [Architecture technique](Architecture-Technique)  
→ Vision produit : [Vision et objectif](Vision-et-Objectif)

## Objectif

Construire **Resonance** : une interface provider-neutral au-dessus du moteur Python existant, sans dupliquer la logique métier dans Swift.

| Principe | Signification |
|----------|---------------|
| **Contrats d'abord** | Les DTO Python (`ui/shared`) sont l'API entre moteur et shells |
| **Un moteur, plusieurs shells** | CLI, app macOS, iOS futur |
| **Inward dependencies** | L'UI n'importe jamais Apple Music, AppleScript ou les providers |
| **Non destructif** | Aucune suppression playlist/bibliothèque dans l'UI |

## Feuille de route Phase 4

| PR | Livrable | Statut |
|----|----------|--------|
| **4.0** | Discovery produit + ADR-011 | ✅ |
| **4.1** | DTO partagés + validation pure | ✅ |
| **4.2** | Engine Bridge JSON-lines | ✅ |
| **4.3** | Theme engine Python (JSON tokens) | ✅ |
| **4.4** | Shell macOS SwiftUI (Accueil + Paramètres) | ✅ |
| **4.5** | Formulaire Nouvelle Playlist + preview | ✅ |
| **4.6** | Import UX + bridge runtime Python | ✅ |
| **4.7** | Laboratoire + historique | 📋 |
| **4.9** | Shell iOS / iPadOS | 📋 |

## Structure du dépôt

```text
playlist_builder/
  ui/
    shared/          # DTO, validation, navigation, thèmes
    bridge/          # Protocole JSON Engine Bridge (provider-neutral)
  app/
    bridge_runtime/  # Runtime moteur ↔ bridge (Phase 4.6)
  integration/       # Providers (Apple Music isolé)
  app/use_cases/     # Cas d'usage métier

apps/resonance/      # App macOS SwiftUI
  ResonanceCore/     # DTO, BridgeClient, validation
  ResonanceDesign/   # ThemeManager + tokens JSON
  ResonanceMac/      # Exécutable SwiftUI + import UX
```

## Phase 4.2 — Engine Bridge

Protocole JSON-lines entre shells SwiftUI et le moteur Python :

| Commande | Rôle |
|----------|------|
| `list_providers` | Liste des providers disponibles |
| `validate_generation_request` | Validation métier |
| `generate_playlist` | Génération réelle |
| `import_playlist` | Import vers Apple Music (streamé) |
| `continue_manual_acquisition` | Reprise après ajout manuel Music.app |
| `diagnostics` | Version moteur / événements |

Codes d'erreur stables : `invalid_request`, `validation_failed`, `engine_error`, `provider_unavailable`, `manual_action_required`.

Point d'entrée runtime :

```bash
python3 -m playlist_builder.cli.engine_bridge
```

## Phase 4.4 — Shell macOS

```bash
cd apps/resonance
swift build && swift run ResonanceMac
```

Navigation sidebar :

| Écran | Statut |
|-------|--------|
| Accueil | ✅ MVP |
| Nouvelle Playlist | ✅ formulaire + génération + import |
| Historique | 📋 placeholder |
| Laboratoire | 📋 placeholder |
| Paramètres | ✅ sélecteur de thème |

## Phase 4.5 — Builder playlist

Formulaire aligné sur `PlaylistGenerationRequest` :

- Nom, description, seeds, mots-clés, taille, énergie, exclusions
- Validation UI (mêmes règles que Python 4.1)
- Bouton **Générer** → preview moteur Python (ou mock si bridge indisponible)

## Phase 4.6 — Import UX + moteur connecté

Flux depuis la preview :

1. **Importer dans Apple Music** — lance `import_playlist` via bridge
2. **Progression** — résolution, cache IdentityCache, catalogue, acquisition
3. **Acquisition manuelle** — instruction claire + bouton « J'ai ajouté le morceau, continuer »
4. **Rapport** — morceaux ajoutés, ignorés, introuvables, erreurs (style laboratoire)

**Limitation documentée (4.6b)** : un process Python par commande ; pas de streaming live pendant l'exécution. Fonctionnel sur macOS avec Music.app.

Toute la logique Apple Music reste côté Python — aucun AppleScript ni MusicKit dans Swift.

## Lancer les tests

```bash
# Python (tout le repo)
python3 -m pytest -q

# Swift (macOS uniquement)
cd apps/resonance && ./scripts/build.sh
```

## Documentation technique (repo)

- `docs/product/phase-4-import-ux.md` — import UX + critères d'acceptation
- `docs/product/phase-4-playlist-builder.md` — formulaire 4.5
- `docs/product/phase-4-6-bridge-runtime.md` — notes runtime
- `docs/architecture/phase-4-ui-architecture.md` — architecture cible

---

*Le moteur reste Python. L'interface devient belle. Comme un PolicyCenter qui garde ses règles — mais avec des playlists.*
