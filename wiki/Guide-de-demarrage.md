# Guide de démarrage rapide

*De zéro à ta première playlist en 10 minutes — le temps de mettre les lunettes de soleil.*

## Pré-requis

| Élément | Obligatoire pour | Détail |
|---------|------------------|--------|
| **macOS** | `create_playlist.py` | AppleScript pilote l'app Musique |
| **App Musique** | Création playlist | Installée et synchronisée iCloud |
| **Python 3.12+** | Tout | StrEnum + dataclass(slots=True), pas de downgrade supporté |
| **Linux/Windows** | `check_catalog.py` seulement | Préparation des rapports catalogue |

## Installation

### Option minimale (recommandée)

```bash
git clone https://github.com/DrCeylon/playlist.git
cd playlist
```

C'est tout. Pas de `pip install` requis pour l'usage de base.

### Option développeur

```bash
pip install -e ".[dev]"
pytest   # lancer les tests
```

Commandes installées :
- `playlist-check-catalog`
- `playlist-create`

## Première exécution — 3 commandes

### 1. Prévisualiser (sans risque)

```bash
python3 create_playlist.py --dry-run
```

Tu verras les 96 morceaux de la playlist Orlando, section par section. Aucune modification dans Apple Music.

### 2. Vérifier le catalogue

```bash
python3 check_catalog.py --country us
```

Génère dans `reports/` :
- `catalog_matches_YYYYMMDD_HHMMSS.csv`
- `catalog_matches_YYYYMMDD_HHMMSS.html`

Ouvre le HTML :

```bash
open reports/catalog_matches_*.html
# ou sur macOS :
zsh tools/open_report.command
```

### 3. Créer la playlist

```bash
python3 create_playlist.py
```

L'app Musique s'ouvre, la playlist est créée ou mise à jour, un rapport TXT est généré.

## Mettre à jour le projet

```bash
cd ~/chemin/vers/playlist
git pull
```

## Structure du dossier

```
playlist/
├── check_catalog.py          # Point d'entrée — vérification catalogue
├── create_playlist.py        # Point d'entrée — création playlist
├── apps/resonance/           # App macOS Resonance (SwiftUI)
│   ├── scripts/build.sh
│   └── scripts/package-mac-app.sh
├── playlists/                # Tes définitions JSON
│   └── orlando_pool_party_2026.json
├── reports/                  # Rapports générés (gitignored)
├── cache/                    # Cache API catalogue (gitignored)
├── playlist_builder/         # Code source du package
├── wiki/                     # Documentation wiki (publiée sur GitHub Wiki)
└── docs/                     # Documentation technique du repo
```

## App macOS Resonance

```bash
cd apps/resonance
./scripts/package-mac-app.sh
open dist/ResonanceMac.app
```

→ [Phase 4 — Interface Resonance](Phase-4-Interface-Resonance) · [Phase 4.8A — Clôture](Phase-4-8A-Cloture)

## Prochaine étape

→ [Workflow complet](Workflow-complet) pour comprendre chaque étape en détail.

## Créer ta propre playlist

1. Copie `playlists/orlando_pool_party_2026.json` → `playlists/ma_playlist.json`
2. Modifie le JSON (voir [Format JSON](Format-JSON-Playlist))
3. Lance :

```bash
python3 check_catalog.py --playlist playlists/ma_playlist.json
python3 create_playlist.py --playlist playlists/ma_playlist.json
```

---

*Tip papa : fais toujours le `--dry-run` avant. Comme relire un contrat avant signature.*
