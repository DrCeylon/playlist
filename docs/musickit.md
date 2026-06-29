# MusicKit / Apple Music API

> **Statut : expérimental — non utilisé en production**
>
> Ce moteur nécessite un **compte Apple Developer payant** (99 USD/an) pour générer les tokens JWT.
> Le workflow recommandé reste **AppleScript + check_catalog.py** (gratuit).

## Quand l'utiliser

- Prototypage de la future app iOS
- Tests avancés sans passer par l'app Musique macOS
- Une fois le compte développeur Apple souscrit

```bash
export APPLE_MUSIC_DEVELOPER_TOKEN="..."
export APPLE_MUSIC_USER_TOKEN="..."
python3 create_playlist.py --engine musickit --storefront us
```

## Variables d'environnement

- `APPLE_MUSIC_DEVELOPER_TOKEN` : JWT signé avec une clé Apple Developer MusicKit
- `APPLE_MUSIC_USER_TOKEN` : token utilisateur autorisant l'accès à la bibliothèque

## Principes produit

- Création de playlists : autorisée
- Mise à jour de playlists : autorisée par ajout de morceaux
- Suppression de playlists : volontairement non supportée
- Suppression de morceaux dans une playlist : volontairement non supportée

## Relation avec l'app iOS

Sur iOS, le framework MusicKit natif remplacera ce client Python. Voir [ios-roadmap.md](ios-roadmap.md).

## Architecture

- `music/client.py` : moteur **recommandé** (AppleScript, macOS, gratuit)
- `music/musickit_client.py` : prototype API REST (expérimental, licence payante)
