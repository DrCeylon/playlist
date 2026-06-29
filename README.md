# Apple Music Playlist Builder

Petit outil macOS pour créer automatiquement des playlists Apple Music à partir de fichiers JSON.

## Playlist incluse

- **🏝 Orlando Pool Party 2026** : pool party Floride, bonne humeur, montée progressive, environ 6 h, sans reggaeton.

## Ce que fait réellement l'outil

AppleScript peut créer une playlist et ajouter des titres qui sont déjà présents dans ta bibliothèque Apple Music/iCloud. En revanche, il ne peut pas ajouter automatiquement à ta bibliothèque des titres du catalogue streaming qui n'y sont pas encore.

La V2 ajoute donc un deuxième outil :

- `check_catalog.py` vérifie les titres dans le catalogue public Apple/iTunes ;
- il génère un rapport HTML avec les liens Apple Music ;
- tu peux ouvrir les titres manquants, les ajouter à ta bibliothèque, puis relancer `create_playlist.py`.

C'est le workflow le plus fiable sans passer par un vrai accès MusicKit développeur Apple.

## Pré-requis

- macOS
- App **Music / Musique** ouverte ou installée
- Python 3
- Synchronisation de la bibliothèque Apple Music activée

## Mise à jour locale

Dans ton dossier déjà cloné :

```bash
cd ~/Music/Playlist/playlist
git pull
```

## 1. Vérifier la playlist côté catalogue Apple

```bash
python3 check_catalog.py --country us
```

Le script génère :

- `reports/catalog_matches_YYYYMMDD_HHMMSS.csv`
- `reports/catalog_matches_YYYYMMDD_HHMMSS.html`

Pour ouvrir le rapport HTML :

```bash
open reports/catalog_matches_*.html
```

Ou :

```bash
zsh tools/open_report.command
```

## 2. Créer la playlist depuis les morceaux déjà disponibles dans ta bibliothèque

```bash
python3 create_playlist.py
```

## 3. Compléter les morceaux manquants

Si beaucoup de titres sont non trouvés :

1. ouvre le rapport HTML ;
2. clique sur les titres importants ;
3. ajoute-les à ta bibliothèque Apple Music ;
4. relance :

```bash
python3 create_playlist.py
```

Le script évite les doublons par défaut.

## Téléchargement hors connexion

Une fois la playlist créée dans Apple Music :

1. ouvrir la playlist **🏝 Orlando Pool Party 2026** ;
2. cliquer sur le bouton de téléchargement ;
3. laisser Apple Music télécharger les morceaux.

## Notes importantes

Un rapport est généré dans le dossier `reports/` après chaque exécution.
