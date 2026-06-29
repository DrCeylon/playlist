# Feuille de route iOS

*Générer des playlists depuis l'iPhone — le projet qui me fait lever le matin.*

## Pourquoi iOS ?

Le workflow macOS actuel fonctionne. Mais je ne veux pas ouvrir le Mac pour créer une playlist quand je suis au bord de la piscine avec **Arthur et Léonard**.

L'objectif : une **app SwiftUI** sur iPhone qui :
1. Charge un JSON playlist (ou génère depuis des seeds — Phase 2)
2. Prévisualise les sections
3. Crée la playlist dans Apple Music en un tap

## Architecture cible

```
┌─────────────────────────────────────┐
│           App iOS (SwiftUI)         │
│  ┌─────────┐  ┌──────────────────┐  │
│  │   UI    │  │  Domain Layer    │  │
│  │ Sections│  │  (porté Python) │  │
│  │ Preview │  │  Loader, Scoring│  │
│  │ Actions │  │  Planner         │  │
│  └─────────┘  └────────┬─────────┘  │
└──────────────────────────┼──────────┘
                           │
              ┌────────────▼────────────┐
              │   MusicKit (natif iOS)  │
              │   Catalogue + Bibliothèque│
              └─────────────────────────┘
```

## Modules Python → Swift

| Python (actuel) | Swift (cible) | Priorité |
|-----------------|---------------|----------|
| `core/models.py` | `TrackRef`, `PlaylistDefinition` | P0 |
| `playlists/loader.py` | `Codable` JSON decoder | P0 |
| `catalog/scoring.py` | `CatalogScoring.swift` | P0 |
| `catalog/apple_search.py` | iTunes Search (URLSession) | P1 |
| `planning/planner.py` | `PlaylistPlanner` | P1 |
| `generation/generator.py` | `PlaylistGenerator` | P1 |
| `music/musickit_client.py` | MusicKit framework natif | P0 |
| `music/client.py` (AppleScript) | ❌ Non applicable iOS | — |

## Contrat JSON stable

Le schéma JSON ne changera pas — c'est le **contrat** entre l'outil Python, l'app iOS, et les fichiers partagés (iCloud, AirDrop, Files).

```json
{
  "name": "...",
  "description": "...",
  "sections": [
    {
      "name": "...",
      "songs": [{"artist": "...", "title": "..."}]
    }
  ]
}
```

Import possible depuis :
- Fichier local (Files app)
- iCloud Drive
- AirDrop depuis le Mac
- Génération in-app (Phase 2)

## MusicKit sur iOS vs API REST

| Aspect | Python REST (actuel) | iOS natif (cible) |
|--------|---------------------|-------------------|
| Auth | JWT manuel + user token | Compte Apple Music utilisateur |
| Coût dev | 99 USD/an | Inclus dans compte dev app |
| Expérience | CLI terminal | UI native, un tap |
| Catalogue | API REST | Framework `MusicKit` |

**Bonne nouvelle** : sur iOS, MusicKit natif ne nécessite pas la même gymnastique JWT que le prototype Python — l'OS gère l'authentification utilisateur.

## Phases de développement iOS

### Phase iOS-1 — MVP

- [ ] Projet Xcode SwiftUI
- [ ] Import JSON playlist
- [ ] Prévisualisation par sections
- [ ] Création playlist via MusicKit
- [ ] Respect ordre des sections

### Phase iOS-2 — Génération

- [ ] UI seeds + contraintes (porter `planning/`)
- [ ] Scoring et suggestions
- [ ] Export JSON

### Phase iOS-3 — Polish

- [ ] Widget « dernière playlist »
- [ ] Partage AirDrop
- [ ] Thème pool party 🏝
- [ ] Mode Arthur & Léonard (playlist kids)

## Principes produit iOS

Identiques au projet Python :

- **Non destructif** — pas de suppression de playlists
- **Ordre des sections sacré**
- **Gratuit pour l'utilisateur final** — pas d'abonnement app
- **Hors ligne** — téléchargement playlist après création

## Ce que j'apprends en construisant ça

- Swift et SwiftUI (nouveau territoire — reconstruction)
- MusicKit iOS (complémentaire du métier Guidewire, pas un remplacement)
- Product design pour mes propres besoins (le meilleur type de client)

## Timeline

Pas de date fixe. Le projet avance entre :
- Les deliveries Guidewire
- Les devoirs de Arthur et Léonard
- Les pool parties

Chaque commit Python rapproche l'iOS — les modèles et le JSON sont déjà prêts.

---

*Construire une app pour ses enfants et pour soi. C'est le meilleur type de projet. Courageux, fun, et sans reggaeton.*
