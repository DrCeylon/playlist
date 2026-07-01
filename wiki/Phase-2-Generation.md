# Phase 2 — Génération intelligente

*Le cœur de la vision — de « j'ai une liste » à « j'ai une vibe ».*

→ Contexte : [Vision et objectif](Vision-et-Objectif)  
→ Interface : [Phase 4 — Resonance](Phase-4-Interface-Resonance)

## Pourquoi la Phase 2 est centrale

La Phase 1 répond à : *« J'ai ma tracklist, crée-la dans Apple Music. »*

La Phase 2 répond à : **« Voici des mots-clés et des morceaux de référence — construis-moi une playlist. »**

C'est l'objectif principal de l'application — aujourd'hui en CLI, demain dans l'app **Resonance**.

## Input utilisateur

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
           Playlist générée (JSON)
                    │
                    ▼
           Apple Music 🎧
```

## Modules concernés

### `playlist_builder/planning/` & `generation/`

| Modèle | Rôle |
|--------|------|
| `PlaylistRequest` | Nom + seeds + contraintes |
| `SeedTrack` | Morceau de référence avec poids |
| `GenerationConstraints` | Durée, énergie, mots-clés, exclusions |
| `GeneratedPlaylist` | Résultat de la planification |

#### Profils d'énergie

| Profil | Description |
|--------|-------------|
| `chill` | Détendu |
| `steady` | Constant |
| `rising` | Montée progressive |
| `party` | Maximum |
| `max_from_start` | Impact immédiat |
| `random` | Exploration |

### Phases 2–3 — Gateway & intégration

| Composant | Rôle |
|-----------|------|
| `integration/gateway/` | Registre providers neutre |
| `integration/apple_music/` | Import, acquisition, livraison |
| `discovery/` | Pipeline candidats catalogue |
| `app/use_cases/` | Cas d'usage orchestrés |

## État actuel

| Fonctionnalité | Statut |
|----------------|--------|
| Modèles de contraintes | ✅ |
| Planification depuis seeds | ✅ |
| `generate_playlist.py` CLI | ✅ |
| Gateway Apple Music E2E | ✅ |
| Contrats UI (`PlaylistGenerationRequest`) | ✅ Phase 4.1 |
| App macOS formulaire génération | ✅ Phase 4.5 |
| Bridge runtime (UI ↔ moteur) | ✅ Phase 4.6 |
| Import Apple Music via l'UI | ✅ Phase 4.6 (macOS) |

## CLI — génération

```bash
python3 generate_playlist.py \
  --name "Ma Pool Party" \
  --seed "Kygo:Firestone" \
  --keywords "tropical,dance,rising" \
  --duration 240 \
  --exclude "country" \
  --output playlists/ma_playlist.json

python3 create_playlist.py --playlist playlists/ma_playlist.json
```

→ Détails : [Commandes et options CLI](Commandes-et-Options)

## Lien avec Resonance (Phase 4)

Le formulaire **Nouvelle Playlist** de l'app macOS reprend exactement les champs de `PlaylistGenerationRequest` :

- Validation identique (Python + Swift)
- Encodage bridge-ready (`validate_generation_request`, `generate_playlist`)
- Preview via moteur Python (Phase 4.6)
- Import Apple Music via bridge (`import_playlist`)

→ [Phase 4 — Interface Resonance](Phase-4-Interface-Resonance)

---

*Phase 2 = donner une intention, recevoir une playlist. La Phase 4 lui donne un visage.*
