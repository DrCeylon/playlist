# MusicKit / Apple Music API

Objectif : créer ou mettre à jour une playlist Apple Music directement depuis le catalogue, sans étape manuelle d'ajout des morceaux dans la bibliothèque locale.

## Statut

Le moteur `musickit` est introduit comme alternative au moteur `applescript`.

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

- `music/client.py` : moteur local AppleScript, utile pour fallback macOS.
- `music/musickit_client.py` : moteur Apple Music API / MusicKit.
- futurs clients iOS/iPadOS : même logique métier, interface SwiftUI.

## Limite actuelle

Le moteur MusicKit est prêt côté code, mais il nécessite de générer et fournir les tokens Apple. Une fois les tokens configurés, il peut chercher les morceaux dans le catalogue et créer ou mettre à jour la playlist dans la bibliothèque utilisateur.
