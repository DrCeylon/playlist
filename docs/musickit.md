# MusicKit / Apple Music API

## Statut

Le moteur `musickit` est conservé dans le code, mais il est actuellement **expérimental**.

La raison est simple : MusicKit nécessite un compte Apple Developer pour générer un Developer Token. Tant que nous ne souhaitons pas payer cette licence, le workflow recommandé reste le moteur AppleScript.

```bash
python3 create_playlist.py
```

## Usage expérimental

```bash
python3 create_playlist.py --engine musickit --storefront us
```

## Variables d'environnement requises

```bash
export APPLE_MUSIC_DEVELOPER_TOKEN="..."
export APPLE_MUSIC_USER_TOKEN="..."
```

- `APPLE_MUSIC_DEVELOPER_TOKEN` : JWT signé avec une clé Apple Developer MusicKit.
- `APPLE_MUSIC_USER_TOKEN` : token utilisateur autorisant l'accès à la bibliothèque Apple Music de l'utilisateur.

## Principes de sécurité produit

- Création de playlists : autorisée.
- Mise à jour de playlists : autorisée par ajout de morceaux.
- Suppression de playlists : volontairement non supportée.
- Suppression de morceaux dans une playlist : volontairement non supportée à ce stade.

## Architecture cible

- `music/client.py` : moteur local AppleScript, utile pour le workflow gratuit macOS.
- `music/musickit_client.py` : moteur Apple Music API / MusicKit, gardé comme option future.
- futurs clients iOS/iPadOS : même logique métier, interface SwiftUI.

## Limite actuelle

Le moteur MusicKit est prêt côté code, mais il nécessite les tokens Apple. Sans licence Apple Developer, il ne doit pas être considéré comme le workflow principal.

## Optimisations déjà prévues

- Cache JSON des identifiants catalogue (`cache/musickit_catalog.json`).
- Détection des doublons via lecture unique de la playlist existante.
- Retry automatique sur HTTP 429 avec backoff.
- Scoring unifié avec le moteur iTunes (`playlist_builder/catalog/scoring.py`).
