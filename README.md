# Apple Music Playlist Builder

Génère des playlists Apple Music à partir de **mots-clés**, de **morceaux de référence**, ou d'un fichier JSON que tu prépares.

📖 **[Documentation complète (Wiki)](https://github.com/DrCeylon/playlist/wiki)** — vision, guides, architecture, FAQ.

**Release v1.0** — voir [docs/RELEASE_PLAN.md](docs/RELEASE_PLAN.md), [limitations connues](docs/KNOWN_LIMITATIONS.md), [matrice de compatibilité](docs/COMPATIBILITY_MATRIX.md).

## Resonance (app macOS)

Le moteur Python est aussi accessible via **Resonance**, une app macOS SwiftUI (`apps/resonance/`) :

- génération de playlists, import streaming, historique ;
- gestionnaire de playlists (preview), sync dry-run (Phase 6.4), **sync apply** push/pull append_only (Phase 6.5), **YouTube Music expérimental** lecture/import (Phase 6.6) ;
- architecture provider-neutral (Phase 6.1+).

État des phases : [wiki/Etat-des-Phases.md](wiki/Etat-des-Phases.md) · dette technique : [docs/TECHNICAL_DEBT.md](docs/TECHNICAL_DEBT.md) · **limitations v1.0** : [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md).

**Validation locale :**

```bash
python3.12 -m pytest -q          # 488 tests
cd apps/resonance && ./scripts/build.sh   # macOS uniquement
```

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
- Python 3.12+
- Synchronisation de la bibliothèque Apple Music activée

`check_catalog.py` peut aussi être exécuté hors macOS pour préparer les rapports catalogue.

## Installation optionnelle

```bash
pip install -e ".[dev]"
```

## Configuration développeur macOS (reproductible)

```bash
cd ~/Music/Playlist/playlist
brew install python@3.12
python3.12 -m venv .venv
source .venv/bin/activate
python --version            # doit afficher Python 3.12.x
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pip install -r requirements-dev.txt
python scripts/check_environment.py
python -m pytest -q
cd apps/resonance && ./scripts/build.sh
swift run ResonanceMac
```

Alternative guidée :

```bash
./scripts/setup_dev.sh
./scripts/check_all.sh
```

Si `python -m pytest -q` affiche une erreur de version Python, le repo est lancé avec un Python < 3.12 : réactive le venv créé avec `python3.12`.

Commandes disponibles après installation :

- `playlist-check-catalog`
- `playlist-create`
- `playlist-generate`

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

## 2. Générer une playlist assistée (optionnel)

```bash
python3 generate_playlist.py \
  --name "Ma Pool Party" \
  --seed "Kygo:Firestone" \
  --keywords "tropical,dance" \
  --duration 240 \
  --output playlists/ma_playlist.json
```

Le JSON généré est compatible avec `create_playlist.py`.

## 3. Créer la playlist avec AppleScript

```bash
python3 create_playlist.py
```

Par défaut, le script **synchronise** la playlist selon l'ordre des sections du JSON (remplace l'ordre existant). Pour ajouter uniquement les morceaux manquants sans réordonner :

```bash
python3 create_playlist.py --incremental
```

## 4. Compléter les morceaux manquants

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

## Licence & contribution

- [MIT](LICENSE)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
