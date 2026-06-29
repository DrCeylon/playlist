# Sprint 2 — Candidate Discovery Engine

## Objectif

Transformer une intention musicale (`PlaylistRequest`) en un pool de morceaux candidats, puis générer une playlist cohérente, analysable et explicable.

## Pipeline cible

```text
PlaylistRequest
  └── build_discovery_queries
        ├── seeds
        ├── preferred_terms
        └── inclusions
  └── DiscoveryPipeline
        └── CandidateProvider(s)
  └── CandidatePool
        └── deduplication
  └── PlaylistPlanner
        ├── contraintes
        ├── exclusions
        ├── qualité plutôt que quantité
        └── suggestions
  └── PlaylistAnalyzer
  └── Rapport du labo musical
```

## Nouveaux concepts

| Concept | Rôle |
|---------|------|
| `DiscoveryQuery` | Requête concrète dérivée des seeds/inclusions |
| `CandidateProvider` | Abstraction de source de candidats |
| `CandidatePool` | Pool dédupliqué et traçable |
| `DiscoveryPipeline` | Orchestration des providers |
| `GenerationSession` | Agrégat complet d'une tentative de génération |
| `GenerationSessionEngine` | Pipeline complet discovery → planning → analysis → report |

## Philosophie produit

- Mieux vaut 70 excellents morceaux que 300 moyens.
- Une exclusion utilisateur doit être visible, explicable et répétable.
- La génération doit produire un rapport minimaliste, fun et utile.
- Aucune suppression de playlist ou de morceau n'est introduite.

## Prochaine étape

- Brancher `ITunesCandidateProvider` dans une CLI `generate_playlist.py`
- Exporter le `GeneratedPlaylist` en JSON prêt pour `create_playlist.py`
- Ajouter une découverte multi-résultats par requête catalogue

## Correctifs Sprint 2.1

- Les **seeds** sont toujours injectés et priorisés dans la sélection finale
- Le provider iTunes mappe désormais **genre / album / explicit** depuis les métadonnées brutes
- Les requêtes catalogue sont **dédupliquées par terme** et plafonnées pour limiter la latence
