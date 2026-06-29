# Phase 2 — Génération intelligente

*Le cœur de la vision — de « j'ai une liste » à « j'ai une vibe ».*

→ Contexte : [Vision et objectif](Vision-et-Objectif)

## Pourquoi la Phase 2 est centrale

La Phase 1 répond à : *« J'ai ma tracklist, crée-la dans Apple Music. »*

La Phase 2 répond à : **« Voici des mots-clés et des morceaux de référence — construis-moi une playlist. »**

C'est l'objectif principal de l'application. La Phase 1 est le socle fiable ; la Phase 2 est la raison d'être long terme.

## Input utilisateur (cible)

```
┌─────────────────────────────────────────┐
│  Morceaux de référence (seeds)          │
│  → Kygo – Firestone, Avicii – Levels    │
├─────────────────────────────────────────┤
│  Mots-clés / contraintes                │
│  → tropical, dance, rising, 4h        │
├─────────────────────────────────────────┤
│  Exclusions (optionnel)                 │
│  → reggaeton, explicit… (TON choix)    │
└─────────────────────────────────────────┘
                    │
                    ▼
           Playlist générée
                    │
                    ▼
           Apple Music 🎧
```

## Modules concernés

### `playlist_builder/planning/`

Planification avec contraintes.

```python
from playlist_builder.planning.planner import PlaylistPlanner
from playlist_builder.planning.models import (
    PlaylistRequest, SeedTrack, GenerationConstraints, EnergyProfile
)
```

#### Modèles clés

| Modèle | Rôle |
|--------|------|
| `PlaylistRequest` | Nom + seeds + contraintes |
| `SeedTrack` | Morceau de référence avec poids |
| `GenerationConstraints` | Durée, énergie, mots-clés, exclusions |
| `CandidateTrack` | Morceau candidat scoré |
| `GeneratedPlaylist` | Résultat de la planification |

#### Profils d'énergie

| Profil | Description |
|--------|-------------|
| `chill` | Détendu |
| `steady` | Constant |
| `rising` | Montée progressive |
| `party` | Maximum |

#### Contraintes — liberté totale

```python
GenerationConstraints(
    target_duration_minutes=240,
    energy_profile=EnergyProfile.RISING,
    preferred_terms=("tropical", "dance"),    # mots-clés souhaités
    excluded_terms=("reggaeton",),             # TON exclusion, pas celle du créateur
    allow_explicit=True,
)
```

*Chaque utilisateur définit ses propres `excluded_terms`. L'exemple Orlando sans reggaeton est un choix personnel, pas une règle du moteur.*

### `playlist_builder/generation/`

Générateur déterministe sans effet de bord.

```python
from playlist_builder.generation.generator import PlaylistGenerator
```

- Seeds préservés en premier
- Candidats triés par score
- Déduplication par clé morceau
- Aucun appel Apple Music (pur calcul, testable)

## État actuel

| Fonctionnalité | Statut |
|----------------|--------|
| Modèles de contraintes (mots-clés, exclusions) | ✅ |
| Planification depuis seeds | ✅ |
| Scoring des candidats | ✅ Basique |
| Découverte catalogue via mots-clés | 🚧 À venir |
| Similarité musicale | 📋 Planifié |
| Export JSON → `create_playlist.py` | 📋 Planifié |
| CLI dédiée | 📋 Planifié |

## Cible utilisateur (exemples)

| Profil | Input | Résultat attendu |
|--------|-------|------------------|
| Pool party | seeds tropical + `rising` + 6h | Playlist montée progressive |
| Running | seeds énergiques + `steady` + 45min | Playlist tempo constant |
| Soirée reggaeton | seeds reggaeton + `party` | Playlist festive *(légitime !)* |
| Étude | seeds lo-fi + `chill` + 2h | Playlist calme |
| Papa Orlando | seeds perso + exclusions perso | Playlist Orlando 🏝 |

## CLI cible (futur)

```bash
python3 generate_playlist.py \
  --name "Ma Pool Party" \
  --seed "Kygo:Firestone" \
  --seed "Avicii:Levels" \
  --keywords "tropical,dance,rising" \
  --duration 240 \
  --exclude "country" \
  --output playlists/ma_playlist.json

python3 create_playlist.py --playlist playlists/ma_playlist.json
```

## Lien avec l'app iOS

La Phase 2 est le **cœur de l'expérience mobile** : taper des mots-clés, glisser des morceaux de référence, appuyer sur « Générer ».

→ [Feuille de route iOS](Feuille-de-route-iOS)

---

*Phase 2 = donner une intention, recevoir une playlist. Comme souscrire une police avec des critères — sauf que le sinistre ici, c'est une soirée réussie.*
