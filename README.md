# Apple Music Playlist Builder

Petit outil macOS pour créer automatiquement des playlists Apple Music à partir de fichiers JSON.

## Playlist incluse

- **🏝 Orlando Pool Party 2026** : pool party Floride, bonne humeur, montée progressive, environ 6 h, sans reggaeton.

## Workflow recommandé (gratuit)

AppleScript peut créer une playlist et ajouter des titres déjà présents dans ta bibliothèque Apple Music/iCloud. Il ne peut pas ajouter automatiquement des titres du catalogue streaming absents de ta bibliothèque.

1. **`check_catalog.py`** — vérifie les titres via l'API iTunes publique (gratuite)
2. **Rapport HTML** — ouvre les liens pour ajouter les morceaux manquants à ta bibliothèque
3. **`create_playlist.py`** — crée la playlist en respectant l'ordre des sections du JSON

> MusicKit (API Apple payante, 99 USD/an) est disponible en expérimental mais **non nécessaire** pour l'usage actuel. Voir [docs/musickit.md](docs/musickit.md).

## Feuille de route iOS

L'objectif long terme est une app iPhone pour générer des playlists depuis le téléphone. Voir [docs/ios-roadmap.md](docs/ios-roadmap.md).

## Pré-requis

- macOS pour `create_playlist.py`
- App **Music / Musique** ouverte ou installée
- Python 3.10+
- Synchronisation de la bibliothèque Apple Music activée

`check_catalog.py` peut aussi être exécuté hors macOS pour préparer les rapports catalogue.

## Installation (optionnelle)

```bash
pip install -e ".[dev]"
```

## 1. Vérifier la playlist côté catalogue Apple

```bash
python3 check_catalog.py --country us
```

Génère `reports/catalog_matches_*.csv` et `reports/catalog_matches_*.html`.

```bash
open reports/catalog_matches_*.html
# ou
zsh tools/open_report.command
```

## 2. Créer la playlist (ordre des sections conservé)

Par défaut, la playlist est **synchronisée** avec l'ordre exact des sections du JSON :

```bash
python3 create_playlist.py
```

Mode incrémental (ajoute seulement les morceaux manquants, sans réordonner) :

```bash
python3 create_playlist.py --incremental
```

## 3. Compléter les morceaux manquants

1. Ouvre le rapport HTML
2. Ajoute les titres importants à ta bibliothèque Apple Music
3. Relance `python3 create_playlist.py`

## Téléchargement hors connexion

1. Ouvrir la playlist dans Apple Music
2. Cliquer sur le bouton de téléchargement
3. Laisser Apple Music télécharger les morceaux

## Notes

Un rapport est généré dans `reports/` après chaque exécution.
