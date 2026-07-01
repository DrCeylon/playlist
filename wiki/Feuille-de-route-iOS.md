# Feuille de route iOS & cross-platform

*Resonance sur iPhone et iPad — même moteur Python, shell SwiftUI natif.*

→ Contexte : [Vision et objectif](Vision-et-Objectif)  
→ État macOS : [Phase 4 — Interface Resonance](Phase-4-Interface-Resonance)

## Stratégie (ADR-011)

| Couche | Technologie |
|--------|-------------|
| Moteur playlist | **Python** (inchangé) |
| Contrats UI | DTO partagés (`ui/shared` + `ResonanceCore`) |
| Thèmes | Fichiers JSON `.theme.json` (Python + Swift) |
| Rendu Apple | **SwiftUI** (macOS, iOS, iPadOS) |
| Communication | Engine Bridge JSON-lines |

**Un moteur, plusieurs shells** — pas de réécriture métier en Swift.

## État actuel — macOS d'abord

| Phase | Livrable | Statut |
|-------|----------|--------|
| 4.4 | Shell macOS (sidebar, Accueil, Paramètres) | ✅ |
| 4.5 | Formulaire Nouvelle Playlist + preview | 🚧 |
| 4.6 | Import UX + bridge connecté | 📋 |
| 4.7 | Laboratoire + historique | 📋 |
| 4.9 | Shell iOS / iPadOS | 📋 |

```bash
cd apps/resonance && swift run ResonanceMac
```

## Expérience cible (toutes plateformes)

```
┌─────────────────────────────────┐
│  🎧 Resonance                   │
│                                 │
│  Morceaux de référence :        │
│  [Kygo – Firestone        ] [+] │
│                                 │
│  Mots-clés :                    │
│  [tropical] [dance] [rising]    │
│                                 │
│  Morceaux : [50]  Durée : [180] │
│  Énergie : [Montée progressive]│
│                                 │
│  Exclure : [reggaeton] [+]      │
│                                 │
│  [ Prévisualiser ]  [ Générer ] │
└─────────────────────────────────┘
```

**Phase 4.5** implémente ce formulaire sur macOS (preview mockée).

## Architecture cible

```
┌─────────────────────────────────────────────────┐
│     Shell SwiftUI (Mac / iOS / iPad)            │
│  ResonanceMac  ·  ResonanceIOS (futur)          │
└────────────────────┬────────────────────────────┘
                     │ Engine Bridge (JSON)
┌────────────────────▼────────────────────────────┐
│     Moteur Python (playlist_builder)            │
│  use_cases · gateway · planning · generation   │
└─────────────────────────────────────────────────┘
```

## Modules partagés

| Python (`ui/shared`) | Swift (`ResonanceCore`) |
|----------------------|-------------------------|
| `PlaylistGenerationRequest` | `PlaylistGenerationRequest` |
| `AppRoute` | `AppRoute` / `SidebarItem` |
| `validate_playlist_generation_request` | `PlaylistGenerationValidator` |
| `ThemeRegistry` + `.theme.json` | `ThemeManager` + même JSON |

## Phases iOS (4.9+)

### iOS-1 — Shell & navigation

- [ ] `TabView` / `NavigationStack` miroir des `AppRoute`
- [ ] Accueil + Paramètres
- [ ] Thèmes depuis bundle

### iOS-2 — Builder & import

- [ ] Formulaire Nouvelle Playlist (réutilise ResonanceCore)
- [ ] Bridge runtime vers moteur Python
- [ ] MusicKit pour livraison native iOS

### iOS-3 — Polish

- [ ] Layout adaptatif iPhone / iPad
- [ ] Historique sessions
- [ ] Accessibilité VoiceOver

## Principes (inchangés)

- **Liberté musicale** — zéro jugement, exclusions = choix utilisateur
- **Non destructif** — pas de suppression playlist/bibliothèque
- **Provider-neutral dans l'UI** — pas de logique Apple Music dans SwiftUI
- **Gratuit** pour l'utilisateur final (workflow CLI)

## Nature du projet

Projet **perso** du créateur, ouvert à **tous**. Resonance est le nom produit de l'interface — le repo reste `playlist`.

---

*D'abord macOS, ensuite iPhone. Même moteur, même contrat, même vibe.*
