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

## Durcissement après test réel

Le premier test réel a montré une faiblesse spécifique à AppleScript : quand plusieurs morceaux sont résolus dans un seul script, les entrées vides peuvent être perdues au moment où AppleScript convertit une liste en texte. Le parser Python recevait alors moins de lignes que de morceaux attendus et marquait toute la batch en erreur.

La correction retenue privilégie la robustesse :

- collecte des candidats **par morceau** ;
- ajout des morceaux sélectionnés par batch de `persistent ID` ;
- absence de candidat = `NOT_FOUND`, pas `ERROR` ;
- erreur uniquement si l'étape AppleScript échoue réellement.

Ce choix est volontaire : la collecte par morceau est légèrement moins rapide, mais elle isole les erreurs et respecte la règle produit majeure : une mauvaise résolution ne doit pas bloquer toute la playlist.

## Limite volontaire

Le rapport utilisateur n'expose pas encore les candidats rejetés. C'est la prochaine étape naturelle : afficher les meilleurs candidats et leurs scores dans le rapport "savant fou".

## Roadmap Resolver V3

Le V3 devra introduire une vraie couche de diagnostic et de persistance :

1. `ResolverProvider` abstrait (`AppleScriptProvider`, futur `MusicKitProvider`).
2. Rapport détaillé des candidats : top 3, score, raison du rejet.
3. Cache des résolutions fiables par clé normalisée + `persistent ID`.
4. Mode interactif futur pour trancher les ambiguïtés.
5. Export optionnel de la résolution dans le JSON généré.

La V2 doit rester la base stable et gratuite du workflow AppleScript. Le V3 rendra cette base observable, explicable et préparée pour l'interface graphique.
