# Roadmap iPhone / iPad

Objectif long terme : créer une application iPhone/iPad permettant de créer et mettre à jour des playlists Apple Music.

## Principes produit

- L'application peut créer une playlist.
- L'application peut ajouter des morceaux à une playlist existante.
- L'application peut mettre à jour les métadonnées utiles d'une playlist.
- L'application ne doit pas permettre de supprimer une playlist.
- L'application ne doit pas proposer de suppression destructive par défaut.

## Cible fonctionnelle

### Version 1 — Création guidée

1. Donner un nom à la playlist.
2. Indiquer un ou plusieurs morceaux de référence.
3. Choisir une durée ou un nombre de morceaux.
4. Ajouter des contraintes : énergie, ambiance, exclusions.
5. Générer une proposition.
6. Valider puis créer la playlist.

### Version 2 — Mise à jour

1. Sélectionner une playlist existante.
2. Ajouter de nouveaux morceaux cohérents.
3. Réordonner éventuellement selon l'énergie ou les sections.
4. Ne jamais supprimer la playlist.

## Architecture cible

```text
Core logic
  ├── Playlist request model
  ├── Catalog search
  ├── Similarity engine
  ├── Scoring engine
  ├── Playlist generator
  └── Report / preview model

Interfaces
  ├── CLI Python
  ├── GUI locale Mac
  └── SwiftUI iPhone/iPad
```

## Stratégie technique

- Conserver un schéma JSON stable pour les playlists.
- Isoler la logique métier du transport Apple Music.
- Préparer les futurs modèles `PlaylistRequest`, `SeedTrack`, `GenerationConstraint` et `GeneratedPlaylist`.
- Garder AppleScript comme moteur gratuit local sur Mac.
- Garder MusicKit comme moteur futur officiel pour iOS/iPadOS.

**Phase 4.0** formalise l'architecture UI cross-platform : voir
[product/phase-4-product-brief.md](product/phase-4-product-brief.md) et
[architecture/ADR-011-cross-platform-product-ui.md](architecture/ADR-011-cross-platform-product-ui.md).

## Point d'attention

Une application iOS/iPadOS nécessitera très probablement MusicKit et donc un compte Apple Developer. Tant que ce n'est pas souhaité, le développement peut continuer sur le moteur CLI/AppleScript et l'architecture métier portable.
