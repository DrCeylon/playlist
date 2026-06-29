# Phase 2 — Génération intelligente

*De la playlist manuelle à la playlist assistée — le futur proche.*

## Vision

Aujourd'hui (Phase 1), tu définis **chaque morceau** dans le JSON. C'est précis, contrôlé, prévisible — mon côté PolicyCenter adore.

Demain (Phase 2), tu fournis des **morceaux seeds** et des **contraintes**, et le système propose une playlist complète.

Comme passer de la saisie manuelle d'une police à un **questionnaire intelligent** qui pré-remplit les garanties.

## Modules concernés

### `playlist_builder/planning/`

Planification avec contraintes métier.

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
| `GenerationConstraints` | Durée, énergie, exclusions |
| `CandidateTrack` | Morceau candidat scoré |
| `GeneratedPlaylist` | Résultat de la planification |

#### Profils d'énergie

| Profil | Description |
|--------|-------------|
| `chill` | Détendu |
| `steady` | Constant |
| `rising` | Montée progressive (comme Orlando) |
| `party` | Maximum |

#### Contraintes disponibles

```python
GenerationConstraints(
    target_track_count=30,           # ou target_duration_minutes=180
    energy_profile=EnergyProfile.RISING,
    excluded_terms=("reggaeton",),   # exclusion explicite !
    preferred_terms=("tropical", "dance"),
    allow_explicit=True,
)
```

#### API principale

```python
planner = PlaylistPlanner()

# Depuis seeds uniquement (Phase 2 actuelle)
playlist = planner.plan_from_seeds_only(request)

# Avec candidats externes (futur)
playlist = planner.plan(request, candidates)
```

### `playlist_builder/generation/`

Générateur déterministe sans effet de bord.

```python
from playlist_builder.generation.generator import PlaylistGenerator
from playlist_builder.generation.models import (
    PlaylistRequest, PlaylistCandidate, GenerationConstraint, EnergyProfile
)
```

#### Principes

- **Aucun appel Apple Music** — pur calcul
- **Seeds préservés en premier** — tes morceaux de référence passent toujours
- **Déduplication** par clé `artiste::titre`
- **Tri par score** pour les candidats additionnels
- **Testable** à 100 %

#### API

```python
generator = PlaylistGenerator()
result = generator.build(request, candidates)
# result.tracks → liste ordonnée de TrackRef
```

## État actuel (honest status)

| Fonctionnalité | Statut |
|----------------|--------|
| Modèles de contraintes | ✅ Implémenté |
| Planification depuis seeds | ✅ Implémenté |
| Scoring des candidats | ✅ Basique |
| Découverte catalogue auto | 🚧 À venir |
| Similarité musicale (IA/API) | 📋 Planifié |
| Export JSON playlist | 📋 Planifié |
| Interface CLI dédiée | 📋 Planifié |

## Roadmap Phase 2

```
Phase 2a (actuel)     Modèles + planner + generator déterministes
Phase 2b              Branchement iTunes Search pour candidats
Phase 2c              Scoring avancé (BPM, énergie, genre)
Phase 2d              Export JSON → create_playlist.py
Phase 2e              CLI : playlist-generate --seeds "Kygo:Firestone" --duration 360
```

## Exemple futur (cible)

```bash
python3 generate_playlist.py \
  --name "🏝 Pool Party Arthur & Léonard" \
  --seed "Kygo:Firestone" \
  --seed "Avicii:Levels" \
  --duration 240 \
  --energy rising \
  --exclude reggaeton \
  --output playlists/pool_party_kids.json
```

Puis :

```bash
python3 create_playlist.py --playlist playlists/pool_party_kids.json
```

## Lien avec l'app iOS

Ces modules sont **portables vers Swift** :

| Python | Swift (futur) |
|--------|---------------|
| `planning/models.py` | `struct PlaylistRequest` |
| `planning/scoring.py` | `func rankCandidates()` |
| `generation/generator.py` | `class PlaylistGenerator` |

L'UI iOS appellera la même logique métier — seul le moteur Music change (MusicKit natif).

→ [Feuille de route iOS](Feuille-de-route-iOS)

---

*Phase 2, c'est reconstruire plus intelligemment. Comme reprendre un projet Guidewire en legacy : d'abord les contrats, ensuite l'automatisation.*
