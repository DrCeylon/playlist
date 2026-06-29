# Architecture technique

*Comment c'est construit — pour les curieux et le futur moi sur iOS.*

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    POINTS D'ENTRÉE                          │
│  check_catalog.py          create_playlist.py               │
└────────────┬──────────────────────────┬───────────────────┘
             │                          │
┌────────────▼────────────┐  ┌──────────▼───────────────────┐
│  cli/check_catalog.py   │  │  cli/create_playlist.py      │
└────────────┬────────────┘  └──────────┬───────────────────┘
             │                          │
┌────────────▼──────────────────────────▼───────────────────┐
│                    COUCHE MÉTIER                            │
│  playlists/loader   catalog/   music/   planning/         │
│                     reports/   generation/                │
└────────────┬──────────────────────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────┐
│                    COUCHE CORE                            │
│  core/models   core/applescript   core/platform           │
└───────────────────────────────────────────────────────────┘
```

## Package `playlist_builder`

| Module | Rôle |
|--------|------|
| `core/models.py` | `TrackRef`, `CatalogMatch`, `TrackAddResult`… |
| `core/applescript.py` | Échappement et exécution AppleScript |
| `core/platform.py` | Garde macOS |
| `playlists/loader.py` | Chargement et validation JSON |
| `catalog/apple_search.py` | Client iTunes Search API |
| `catalog/scoring.py` | Scoring des correspondances catalogue |
| `catalog/cache.py` | Cache JSON différé |
| `catalog/rate_limiter.py` | Limitation des appels API |
| `catalog/retry_policy.py` | Backoff sur HTTP 429 |
| `music/client.py` | Client AppleScript (moteur principal) |
| `music/musickit_client.py` | Client MusicKit API (expérimental) |
| `reports/catalog.py` | Rapports CSV/HTML catalogue |
| `reports/playlist.py` | Rapport TXT création playlist |
| `planning/` | Phase 2 — planification intelligente |
| `generation/` | Phase 2 — génération déterministe |

## Moteur AppleScript (`music/client.py`)

### Optimisations

| Technique | Avant | Après |
|-----------|-------|-------|
| Détection doublons | 1 appel AppleScript par morceau | 1 scan initial de la playlist |
| Ajout morceaux | 1 appel par morceau | Lots de 25 morceaux |
| Ordre des résultats | Bug sur skips intercalés | Index préservés |

### Flux `add_tracks`

```
Pour chaque morceau (ordre JSON) :
  ├─ Déjà en playlist ? → SKIPPED
  └─ Sinon → file d'attente batch

Pour chaque batch de 25 :
  └─ 1 script AppleScript → duplicate depuis bibliothèque
```

### AppleScript — bibliothèque

Le script cherche dans `library playlist 1` (bibliothèque principale Music) :
1. Correspondance exacte artiste + titre
2. Fallback : `contains` partiel

## Moteur Catalogue (`catalog/apple_search.py`)

### Scoring

| Critère | Points |
|---------|--------|
| Artiste exact | +50 |
| Artiste partiel (inclusion) | +30 |
| Titre exact | +50 |
| Titre partiel | +30 |
| **Seuil minimum** | **30** |

Score max = 100 (match parfait).

### Résilience

- Rate limiter (0.5s par défaut)
- Retry avec backoff exponentiel + jitter sur HTTP 429
- Cache JSON (`cache/itunes_catalog.json`)
- User-Agent explicite

## Moteur MusicKit (`music/musickit_client.py`)

**Statut : expérimental, non utilisé en production.**

- API REST `https://api.music.apple.com/v1`
- Seuil scoring plus strict (60)
- Cache, retry, déduplication
- Nécessite tokens JWT + user token

→ [MusicKit expérimental](MusicKit-Experimental)

## Phase 2 — Planning & Generation

Deux modules préparent la génération intelligente future :

### `planning/`

```python
PlaylistPlanner.plan(request, candidates)
```

- Entrée : `PlaylistRequest` (seeds + contraintes)
- Sortie : `GeneratedPlaylist` (candidats scorés)
- Profils d'énergie : `chill`, `steady`, `rising`, `party`
- Contraintes : durée cible, exclusions, termes préférés

### `generation/`

```python
PlaylistGenerator.build(request, candidates)
```

- Moteur déterministe sans effet de bord
- Préserve les seeds en premier
- Déduplique par clé morceau
- Prêt pour branchement futur sur API similarité

→ [Phase 2 — Génération](Phase-2-Generation)

## Dépendances

**Aucune dépendance runtime.** Python 3.10+ stdlib uniquement.

Développement : `pytest>=8.0`

## Tests

```bash
python3 -m pytest -q
```

Couverture actuelle :
- Scoring catalogue
- Validation JSON
- Cache
- Client AppleScript (ordre, normalisation)
- Planning et génération Phase 2
- MusicKit (mocks)

## Fichiers générés (gitignored)

| Dossier | Contenu |
|---------|---------|
| `reports/` | CSV, HTML, TXT |
| `cache/` | Cache API iTunes et MusicKit |
| `__pycache__/` | Bytecode Python |

## Analogies Guidewire (pour mes collègues)

| Concept Playlist Builder | Équivalent Guidewire |
|--------------------------|----------------------|
| `loader.py` | Validation PCF / règles de souscription |
| `check_catalog.py` | Vérification externe (tierce partie) |
| `create_playlist.py` | Émission / mise à jour de police |
| `reports/` | Notes et documents ClaimCenter |
| `scoring.py` | Moteur de règles / rating |
| JSON playlist | Contrat / spécification produit |
| Section ordonnée | Phase de parcours sinistre |

---

*Architecture propre, modules découplés, zéro suppression. Comme un bon delivery Guidewire — mais avec plus de Daft Punk.*
