# Sprint 2.2 — Smart Resolver

## Objectif

Remplacer la recherche Apple Music trop stricte par une couche dédiée de résolution de morceaux.

Le problème observé : `MusicClient` cherchait principalement `name == title` et `artist == artist` dans la bibliothèque locale Apple Music. Cette stratégie échoue souvent pour les BO, compilations, remasters, versions live ou titres enrichis.

## Nouvelle architecture

```text
TrackRef
  └── resolver.query.generate_query_variants
        ├── title + artist
        ├── artist + title
        ├── title seul
        ├── section + title
        └── aliases contextuels
  └── AppleScript search library
  └── duplicate first acceptable result to playlist
```

## Nouveaux modules

| Module | Rôle |
|--------|------|
| `resolver.normalization` | Normalisation accents, ponctuation, parenthèses, feat. |
| `resolver.query` | Génération de variantes de recherche ordonnées |
| `resolver.scoring` | Score Python 0-100, prêt pour la V2 multi-candidats |
| `resolver.applescript` | Construction batch AppleScript optimisée |

## Philosophie

- Ne pas patcher la recherche actuelle : isoler la résolution dans un composant réutilisable.
- Rester compatible avec le workflow gratuit AppleScript.
- Préparer la future UI : le resolver pourra exposer les candidats ambigus.
- Préparer MusicKit : les mêmes fonctions de normalisation/scoring seront réutilisables.

## Limite V1

La V1 ajoute plusieurs passes de recherche et choisit le premier résultat acceptable. La V2 exposera tous les candidats pour scoring Python complet et choix utilisateur en cas d'ambiguïté.
