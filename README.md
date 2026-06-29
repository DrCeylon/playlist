# Apple Music Playlist Builder

Petit outil macOS pour créer automatiquement des playlists Apple Music à partir de fichiers JSON.

📖 **[Documentation complète (Wiki)](https://github.com/DrCeylon/playlist/wiki)** — guide, architecture, FAQ et feuille de route iOS.

## Playlist incluse

- **🏝 Orlando Pool Party 2026** : pool party Floride, bonne humeur, montée progressive, environ 6 h, sans reggaeton.

## Workflow recommandé pour le moment

Le workflow gratuit reste basé sur AppleScript :

1. `check_catalog.py` vérifie que les morceaux existent dans le catalogue public Apple/iTunes ;
2. le rapport HTML permet d'ouvrir les titres manquants dans Apple Music ;
3. `create_playlist.py` ajoute à la playlist les morceaux déjà présents dans ta bibliothèque Apple Music/iCloud.

MusicKit reste présent dans le code, mais il est considéré comme **expérimental** tant que nous ne configurons pas de compte Apple Developer.

## Pré-requis

- macOS pour `create_playlist.py`
- App **Music / Musique** ouverte ou installée
- Python 3.10+
- Synchronisation de la bibliothèque Apple Music activée

`check_catalog.py` peut aussi être exécuté hors macOS pour préparer les rapports catalogue.

## Installation optionnelle

```bash
pip install -e ".[dev]"
```

Commandes disponibles après installation :

- `playlist-check-catalog`
- `playlist-create`

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

## 2. Créer la playlist avec AppleScript

```bash
python3 create_playlist.py
```

Le script évite les doublons par défaut.

## 3. Compléter les morceaux manquants

Si beaucoup de titres sont non trouvés :

1. ouvre le rapport HTML ;
2. clique sur les titres importants ;
3. ajoute-les à ta bibliothèque Apple Music ;
4. relance :

```bash
python3 create_playlist.py
```

## Option expérimentale — MusicKit

MusicKit permettrait à terme de créer ou mettre à jour une playlist directement depuis le catalogue, sans étape manuelle. Cette option nécessite cependant un compte Apple Developer payant et des tokens MusicKit.

Voir [docs/musickit.md](docs/musickit.md).

## Téléchargement hors connexion

Une fois la playlist créée dans Apple Music :

1. ouvrir la playlist **🏝 Orlando Pool Party 2026** ;
2. cliquer sur le bouton de téléchargement ;
3. laisser Apple Music télécharger les morceaux.

## Principes produit

- Création de playlists : autorisée.
- Mise à jour de playlists : autorisée.
- Suppression de playlists : non supportée.
- Le workflow par défaut doit rester non destructif.

## Notes importantes

Un rapport est généré dans le dossier `reports/` après chaque exécution.
