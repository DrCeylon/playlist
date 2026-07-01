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

## Premiers écrans (visuels textuels)

*Wireframes alignés sur l'implémentation macOS actuelle — juillet 2026.*

### 1. Shell — Accueil + sidebar

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Resonance                                                    ⚙ Paramètres│
├──────────────┬───────────────────────────────────────────────────────────┤
│ ● Accueil    │  Bienvenue dans Resonance                                 │
│ ○ Nouvelle   │                                                           │
│   Playlist   │  Génère des playlists à partir de mots-clés ou de seeds.  │
│ ○ Historique │  Le moteur Python reste la source de vérité.              │
│ ○ Laboratoire│                                                           │
│              │  ┌─────────────┐  ┌─────────────┐                         │
│              │  │ + Nouvelle  │  │  Thèmes     │                         │
│              │  │   playlist  │  │  (4.4)      │                         │
│              │  └─────────────┘  └─────────────┘                         │
└──────────────┴───────────────────────────────────────────────────────────┘
```

### 2. Nouvelle Playlist — formulaire (4.5)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Nouvelle Playlist                                                        │
├──────────────┬───────────────────────────────────────────────────────────┤
│ sidebar      │  Identité                                                 │
│              │  Nom        [ Orlando Pool Party________________ ]        │
│              │  Description[ Montée progressive, sans reggaeton____ ]    │
│              │                                                           │
│              │  Provider   🎧 Apple Music (sélectionné, MVP)           │
│              │                                                           │
│              │  Graines    Artiste [ Kygo____ ]  Morceau [ Firestone ]   │
│              │  Mots-clés  [ tropical, dance, rising________________ ]   │
│              │  Taille     Morceaux [ 50 ]   Durée [    ] min            │
│              │  Énergie    [ Montée progressive ▼ ]                      │
│              │  Exclusions [ + Ajouter une exclusion ]                   │
│              │                                                           │
│              │                              [ ✨ Générer ]                │
└──────────────┴───────────────────────────────────────────────────────────┘
```

### 3. Preview — résultat moteur Python (4.5 + 4.6)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Orlando Pool Party                                                       │
│ 50 morceaux · score moyen 84 %                                           │
│ Aperçu moteur Python                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│  ▼ Montée                                                                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Firestone          Kygo                              score 92 %   │  │
│  │ Reality            Lost Frequencies                  score 88 %   │  │
│  │ Jubel              Klingande                         score 81 %   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  [ Modifier le formulaire ]          [ ⬇ Importer dans Apple Music ]    │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4. Import — progression (4.6)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Import Apple Music                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│  ████████████████░░░░░░░░░░░░  32 / 50                                   │
│  Résolution des morceaux…                                                │
│  Kygo — Firestone                                                        │
│                                                                          │
│  Laboratoire                                                             │
│  · Cache IdentityCache : Kygo — Firestone                                │
│  · Acquisition catalogue : Kyo — Dernière danse                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 5. Acquisition manuelle Music.app (4.6)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ ⚠ Acquisition manuelle requise                                           │
├──────────────────────────────────────────────────────────────────────────┤
│  Kyo — Dernière danse                                                    │
│  Catalogue : Kyo — Dernière danse                                        │
│                                                                          │
│  Ajoute le morceau à ta bibliothèque dans Music.app,                     │
│  puis confirme ici.                                                      │
│                                                                          │
│              [ J'ai ajouté le morceau, continuer ]                        │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6. Rapport d'import — style laboratoire (4.6)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Rapport d'import                                                         │
│ Orlando Pool Party                                                       │
│ Transfert terminé. Le laboratoire confirme une playlist stable.          │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────────┐ ┌────────┐                       │
│  │ 48     │ │ 2      │ │ 0          │ │ 0      │                       │
│  │ Ajoutés│ │ Ignorés│ │ Introuvables│ │ Erreurs│                       │
│  └────────┘ └────────┘ └────────────┘ └────────┘                       │
│                                                                          │
│  ✓ Firestone — Kygo          Ajouté                                      │
│  ✓ Reality — Lost Freq.      Ajouté                                      │
│  ↩ Levels — Avicii           Déjà présent                                │
│                                                                          │
│                                              [ Fermer ]                  │
└──────────────────────────────────────────────────────────────────────────┘
```

→ Wireframes complets (cible produit) : `docs/product/phase-4-wireframes.md` dans le repo.

## Structure du dépôt

```text
playlist_builder/
  ui/
    shared/          # DTO, validation, navigation, thèmes
    bridge/          # Protocole JSON Engine Bridge (provider-neutral)
  app/
    bridge_runtime/  # Runtime moteur ↔ bridge (Phase 4.6)
    use_cases/       # Cas d'usage métier
  integration/       # Providers (Apple Music isolé)

apps/resonance/      # App macOS SwiftUI
  ResonanceCore/     # DTO, BridgeClient, validation
  ResonanceDesign/   # ThemeManager + tokens JSON
  ResonanceMac/      # Exécutable + import UX
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

Point d'entrée runtime :

```bash
python3 -m playlist_builder.cli.engine_bridge
```

## Phase 4.4 — Shell macOS

```bash
cd apps/resonance
swift build && swift run ResonanceMac
```

| Écran | Statut |
|-------|--------|
| Accueil | ✅ MVP |
| Nouvelle Playlist | ✅ formulaire + génération + import |
| Historique | 📋 placeholder |
| Laboratoire | 📋 placeholder |
| Paramètres | ✅ sélecteur de thème |

## Phase 4.5 — Builder playlist

- Formulaire aligné sur `PlaylistGenerationRequest`
- Validation UI (mêmes règles que Python 4.1)
- **Générer** → preview moteur Python (fallback mock si bridge indisponible)

## Phase 4.6 — Import UX + moteur connecté

1. **Importer dans Apple Music** depuis la preview
2. **Progression** — résolution, cache, catalogue
3. **Acquisition manuelle** si nécessaire
4. **Rapport** final

**Limitation (4.6b)** : un process Python par commande bridge ; pas de streaming live pendant l'exécution. Fonctionnel sur **macOS** avec Music.app.

## Lancer les tests

```bash
python3 -m pytest -q
cd apps/resonance && ./scripts/build.sh   # macOS
```

## Documentation technique (repo)

- `docs/product/phase-4-import-ux.md`
- `docs/product/phase-4-playlist-builder.md`
- `docs/architecture/phase-4-ui-architecture.md`

---

*Le moteur reste Python. L'interface devient belle.*
