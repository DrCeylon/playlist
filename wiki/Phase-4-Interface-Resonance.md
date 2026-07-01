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
| **4.5** | Formulaire Nouvelle Playlist + preview mock | 🚧 PR #23 |
| **4.6** | Import UX + bridge runtime | 📋 |
| **4.7** | Laboratoire + historique | 📋 |
| **4.9** | Shell iOS / iPadOS | 📋 |

## Structure du dépôt

```text
playlist_builder/
  ui/
    shared/          # DTO, validation, navigation, thèmes
    bridge/          # Protocole JSON Engine Bridge
  integration/       # Providers (Apple Music isolé)
  app/use_cases/     # Cas d'usage métier

apps/resonance/      # App macOS SwiftUI
  ResonanceCore/     # Miroir des contrats (routes, DTO, validation)
  ResonanceDesign/   # ThemeManager + tokens JSON
  ResonanceMac/      # Exécutable SwiftUI
```

## Phase 4.1 — Contrats partagés

Package `playlist_builder/ui/shared/` :

| Module | Contenu |
|--------|---------|
| `dto/` | `PlaylistGenerationRequest`, `ProviderOption`, `ImportProgressState`… |
| `validation/` | Validateurs purs (français, sans I/O) |
| `navigation/` | `AppRoute` (sidebar macOS / tabs iOS) |
| `state/` | `UiScreenState` |

## Phase 4.2 — Engine Bridge

Protocole JSON-lines entre shells SwiftUI et le moteur Python :

| Commande | Rôle |
|----------|------|
| `list_providers` | Liste des providers disponibles |
| `validate_generation_request` | Validation métier |
| `generate_playlist` | Génération |
| `import_playlist` | Import vers bibliothèque |
| `diagnostics` | Événements laboratoire |

Codes d'erreur stables : `invalid_request`, `validation_failed`, `engine_error`.

## Phase 4.3 — Moteur de thèmes

- `ThemeRegistry` charge les fichiers `.theme.json`
- Héritage `extends` (ex. Classic Laboratory → Apple Music Dark)
- 3 thèmes embarqués : `apple_music_light`, `apple_music_dark`, `classic_winamp_inspired`
- Swift lit les **mêmes JSON** depuis le bundle

## Phase 4.4 — Shell macOS

App lançable :

```bash
cd apps/resonance
swift build && swift run ResonanceMac
```

Navigation sidebar :

| Écran | Statut |
|-------|--------|
| Accueil | ✅ MVP |
| Nouvelle Playlist | 🚧 Phase 4.5 |
| Historique | 📋 placeholder |
| Laboratoire | 📋 placeholder |
| Paramètres | ✅ sélecteur de thème |

## Phase 4.5 — Builder playlist (en cours)

Formulaire complet aligné sur `PlaylistGenerationRequest` :

- Nom, description, seeds, mots-clés
- Nombre de morceaux / durée cible
- Courbe d'énergie, exclusions visibles
- Validation UI (mêmes règles que Python 4.1)
- Bouton **Générer** → preview mockée (bridge-ready, pas encore connecté)

## Lancer les tests

```bash
# Python (tout le repo)
python3 -m pytest -q

# Swift (macOS uniquement)
cd apps/resonance && ./scripts/build.sh
```

## Documentation technique (repo)

Les specs détaillées vivent dans `docs/` :

- `docs/architecture/phase-4-ui-architecture.md`
- `docs/product/phase-4-macos-shell.md`
- `docs/product/phase-4-playlist-builder.md`
- `docs/product/theme-engine.md`

---

*Le moteur reste Python. L'interface devient belle. Comme un PolicyCenter qui garde ses règles — mais avec des playlists.*
