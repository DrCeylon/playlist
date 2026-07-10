# YouTube Music — guide expérimental (Phase 6.6)

YouTube Music est un **provider expérimental** (`ProviderCapability.experimental`). Il n’est pas requis pour utiliser Resonance.

## Installation optionnelle

```bash
pip install "playlist-builder[youtube]"
```

Sans cette dépendance, Resonance démarre normalement. L’onglet Providers affiche YouTube Music comme indisponible avec un message explicite.

## Authentification (bibliothèque personnelle)

1. Exportez vos en-têtes navigateur avec l’outil documenté par [ytmusicapi](https://ytmusicapi.readthedocs.io/) (`ytmusicapi oauth` ou export headers JSON).
2. Enregistrez le fichier **en dehors du dépôt** (ex. `~/Library/Application Support/Resonance/youtube_headers.json`).
3. Connectez via le bridge :

```json
{
  "command": "provider_connect",
  "params": {
    "provider_id": "youtube_music",
    "headers_file_path": "/chemin/vers/headers.json",
    "display_name": "Mon compte"
  }
}
```

Resonance ne stocke que le **chemin** du fichier localement (`data/provider_auth/youtube_music.json`). Le contenu des cookies n’est jamais écrit dans les logs, snapshots ou opérations de sync.

## Playlist publique (sans compte)

Avec `ytmusicapi` installé :

```json
{
  "command": "get_remote_playlist",
  "params": {
    "provider_id": "youtube_music",
    "remote_playlist_id": "PLxxxxxxxx"
  }
}
```

Vous pouvez aussi fournir une URL `https://music.youtube.com/playlist?list=...`.

## Fallback fichier (toujours disponible)

```json
{
  "command": "load_remote_playlist_from_file",
  "params": {
    "file_path": "/chemin/playlist.csv",
    "provider_id": "youtube_music",
    "playlist_name": "Ma playlist"
  }
}
```

Formats supportés : JSON (`tracks[]` avec `artist`, `title`) ou CSV (`artist`, `title`, `album`, `position`).

Enchaînement recommandé : `get_remote_playlist` ou `load_remote_playlist_from_file` → `import_remote_playlist` → `plan_sync`.

## Limitations Phase 6.6

- **Pas d’écriture distante** (`playlist_write = None`, pas de `PLAYLIST_SYNC`).
- `apply_sync` vers YouTube Music est refusé proprement.
- API non officielle — peut casser sans préavis.
- Conformité ToS : responsabilité de l’utilisateur.
