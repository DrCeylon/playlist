# Sprint 2.3 — Smart Resolver V2

## Objectif

Faire passer le resolver d'une logique `premier résultat utilisable` à une logique `collecte de candidats → scoring Python → sélection du meilleur`.

## Pipeline

```text
TrackRef
  ├── Query variants
  ├── AppleScript candidate collection
  ├── ResolverCandidate[]
  ├── Python score_candidate()
  ├── ResolverDecision
  └── duplicate persistent ID to target playlist
```

## Pourquoi c'est meilleur

La V1 choisissait souvent le premier résultat retourné par Apple Music. La V2 sépare clairement :

1. AppleScript collecte les candidats.
2. Python décide.
3. AppleScript ajoute uniquement le `persistent ID` sélectionné.

Cela améliore fortement :

- la qualité du matching ;
- la traçabilité ;
- la future interface de résolution d'ambiguïtés ;
- la compatibilité avec MusicKit si on l'ajoute plus tard.

## Nouveaux modules

| Module | Rôle |
|--------|------|
| `resolver.models` | `ResolverCandidate`, `ResolverDecision` |
| `resolver.selection` | ranking, déduplication, sélection du meilleur candidat |
| `resolver.applescript` | collecte candidats + duplication par persistent ID |

## Limite volontaire

Le rapport utilisateur n'expose pas encore les candidats rejetés. C'est la prochaine étape naturelle : afficher les meilleurs candidats et leurs scores dans le rapport "savant fou".
