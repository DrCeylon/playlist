# Feuille de route iOS

*Générer des playlists depuis l'iPhone — pour tout le monde.*

→ Contexte : [Vision et objectif](Vision-et-Objectif)

## Objectif

Une **app iOS** où n'importe qui peut :

1. Saisir des **mots-clés** et/ou des **morceaux de référence**
2. Prévisualiser la playlist générée par sections
3. La créer dans Apple Music en un tap

Pas besoin d'un Mac. Pas besoin de JSON. Pas besoin d'être le créateur du repo.

## Public cible

**Tout le monde** — pas seulement le créateur ou sa famille.

| Utilisateur | Cas d'usage |
|-------------|-------------|
| Toi | Pool party, running, soirée |
| Un ami | Sa playlist anniversaire |
| Un inconnu sur GitHub | Fork, adapte, crée la sienne |
| Arthur & Léonard (un jour) | Leur playlist kids sur iPad |

## Expérience cible

```
┌─────────────────────────────────┐
│  🎧 Playlist Builder            │
│                                 │
│  Morceaux de référence :        │
│  [Kygo – Firestone        ] [+] │
│  [Avicii – Levels         ] [+] │
│                                 │
│  Mots-clés :                    │
│  [tropical] [dance] [rising]    │
│                                 │
│  Durée : [4h ▼]  Énergie : [↗] │
│                                 │
│  Exclure : [reggaeton] [+]      │
│  (optionnel — ton choix)        │
│                                 │
│  [ Prévisualiser ]  [ Générer ] │
└─────────────────────────────────┘
```

## Architecture cible

```
┌─────────────────────────────────────┐
│           App iOS (SwiftUI)         │
│  ┌─────────┐  ┌──────────────────┐  │
│  │   UI    │  │  Domain Layer    │  │
│  │ Keywords│  │  Loader, Scoring│  │
│  │ Seeds   │  │  Planner         │  │
│  │ Preview │  │  Generator       │  │
│  └─────────┘  └────────┬─────────┘  │
└──────────────────────────┼──────────┘
                           │
              ┌────────────▼────────────┐
              │   MusicKit (natif iOS)  │
              └─────────────────────────┘
```

## Modules Python → Swift

| Python | Swift | Priorité |
|--------|-------|----------|
| `planning/models.py` | `PlaylistRequest`, contraintes | P0 |
| `planning/scoring.py` | `rankCandidates()` | P0 |
| `generation/generator.py` | `PlaylistGenerator` | P0 |
| `playlists/loader.py` | `Codable` JSON | P1 |
| `catalog/scoring.py` | `CatalogScoring` | P1 |
| MusicKit natif iOS | Remplace `musickit_client.py` | P0 |

## Phases iOS

### iOS-1 — MVP génération

- [ ] Saisie mots-clés + morceaux de référence
- [ ] Génération playlist (porter Phase 2)
- [ ] Prévisualisation par sections
- [ ] Création Apple Music via MusicKit

### iOS-2 — Import & partage

- [ ] Import JSON existant
- [ ] Export JSON
- [ ] Partage AirDrop / Files

### iOS-3 — Polish

- [ ] UI soignée, accessible
- [ ] Historique des playlists générées
- [ ] Mode hors ligne (téléchargement)

## Principes iOS

Identiques au projet Python :

- **Liberté musicale** — zéro jugement, exclusions = choix utilisateur
- **Non destructif** — pas de suppression
- **Gratuit** pour l'utilisateur final
- **Projet perso** — pas d'abonnement, pas de pub

## Nature du projet

Projet **perso** du créateur, ouvert à **tous**. Pas une startup, pas un produit commercial. Un outil qu'il aurait aimé avoir — et qu'il partage.

---

*Un iPhone, quelques mots-clés, une playlist. Pour tout le monde. Même pour ceux qui aiment le reggaeton.*
