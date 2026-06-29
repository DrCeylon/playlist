# Feuille de route iOS

Objectif long terme : une app iOS native pour générer des playlists Apple Music directement depuis l'iPhone.

## Workflow actuel (Python / macOS)

1. `check_catalog.py` — vérification catalogue via iTunes Search API (gratuit)
2. `create_playlist.py` — création via AppleScript (gratuit, macOS)
3. MusicKit API — **réservé au futur**, nécessite un compte Apple Developer payant (99 USD/an)

## Modules portables vers Swift

Ces modules Python sont conçus pour être réimplémentés tels quels en Swift :

| Module Python | Équivalent Swift prévu |
|---------------|------------------------|
| `core/models.py` | `TrackRef`, `PlaylistSection`, `PlaylistDefinition` |
| `playlists/loader.py` | Décodage `Codable` du JSON playlist |
| `catalog/scoring.py` | Fonction de scoring catalogue partagée |
| `catalog/apple_search.py` | iTunes Search API (gratuit, utilisable depuis iOS) |

## Moteur iOS cible

Sur iOS, le moteur recommandé sera **MusicKit natif** (framework `MusicKit` / `MediaPlayer`) :

- Pas de AppleScript (indisponible sur iPhone)
- Accès direct au catalogue et à la bibliothèque utilisateur
- Authentification via le compte Apple Music de l'utilisateur (pas de JWT développeur côté app grand public si l'app utilise MusicKit standard)

Le code Python `music/musickit_client.py` sert de **prototype de référence** pour la logique métier (recherche, scoring, création de playlist), pas comme moteur de production actuel.

## Ordre des sections

Le JSON définit des `sections` ordonnées. Chaque section contient une liste ordonnée de `songs`.

Règle produit : **l'ordre final de la playlist doit suivre l'ordre des sections puis l'ordre des morceaux dans chaque section**.

Implémentation macOS actuelle :

- Par défaut, `create_playlist.py` synchronise la playlist (`sync_playlist_order`) : vide la playlist puis reconstruit dans l'ordre du JSON.
- `--incremental` conserve l'ancien comportement (ajout des morceaux manquants à la fin).

## Structure JSON (contrat stable)

```json
{
  "name": "Ma Playlist",
  "description": "Optionnel",
  "sections": [
    {
      "name": "Section 1",
      "songs": [
        {"artist": "Artiste", "title": "Titre"}
      ]
    }
  ]
}
```

Ce schéma est le contrat partagé entre l'outil Python actuel et la future app iOS.

## Prochaines étapes iOS

1. Projet Xcode SwiftUI + MusicKit
2. Réutiliser le schéma JSON (import fichier ou iCloud)
3. Porter `scoring.py` en Swift
4. UI : sélection playlist → prévisualisation par sections → génération
5. Tests unitaires Swift sur le scoring et le parsing JSON
