# Apple Music Playlist Builder

Petit outil macOS pour créer automatiquement des playlists Apple Music à partir de fichiers JSON.

## Playlist incluse

- **🏝 Orlando Pool Party 2026** : pool party Floride, bonne humeur, montée progressive, environ 6 h, sans reggaeton.

## Pré-requis

- macOS
- App **Music / Musique** ouverte ou installée
- Python 3
- Synchronisation de la bibliothèque Apple Music activée

## Installation locale

```bash
cd ~/Music/Playlist

git clone https://github.com/DrCeylon/playlist.git .
```

Si le dossier n'est pas vide :

```bash
git clone https://github.com/DrCeylon/playlist.git AppleMusicPlaylistBuilder
cd AppleMusicPlaylistBuilder
```

## Test de la playlist sans rien modifier

```bash
python3 create_playlist.py --dry-run
```

## Création dans Apple Music

```bash
python3 create_playlist.py
```

Au premier lancement, macOS demandera l'autorisation pour que Python contrôle l'application **Musique**. Il faut accepter.

## Téléchargement hors connexion

Une fois la playlist créée dans Apple Music :

1. ouvrir la playlist **🏝 Orlando Pool Party 2026** ;
2. cliquer sur le bouton de téléchargement ;
3. laisser Apple Music télécharger les morceaux.

## Notes importantes

Le script cherche les morceaux dans ta bibliothèque Apple Music. Si un morceau n'est pas trouvé, ajoute-le une fois à ta bibliothèque, puis relance le script.

Un rapport est généré dans le dossier `reports/` après chaque exécution.
