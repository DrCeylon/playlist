# Commandes et options CLI

*La référence complète — tous les flags, tous les cas.*

## `check_catalog.py`

Vérifie les morceaux contre le catalogue public Apple/iTunes.

### Usage

```bash
python3 check_catalog.py [OPTIONS]
# ou après pip install :
playlist-check-catalog [OPTIONS]
```

### Options

| Option | Défaut | Description |
|--------|--------|-------------|
| `--playlist PATH` | `playlists/orlando_pool_party_2026.json` | Fichier JSON à vérifier |
| `--country CODE` | `us` | Store iTunes (`us`, `ch`, `fr`, `de`…) |
| `--sleep SECONDS` | `0.5` | Délai minimum entre appels API |
| `--cache PATH` | `cache/itunes_catalog.json` | Fichier cache JSON |
| `--no-cache` | désactivé | Ignore le cache (re-vérifie tout) |

### Exemples

```bash
# Store suisse
python3 check_catalog.py --country ch

# Playlist personnalisée, cache désactivé
python3 check_catalog.py --playlist playlists/ma_fete.json --no-cache

# Plus lent (évite le rate limiting)
python3 check_catalog.py --sleep 1.0
```

### Sorties

- `reports/catalog_matches_YYYYMMDD_HHMMSS.csv`
- `reports/catalog_matches_YYYYMMDD_HHMMSS.html`

### Code de sortie

| Code | Signification |
|------|---------------|
| `0` | Succès |
| `1` | Fichier introuvable ou JSON invalide |

---

## `create_playlist.py`

Crée ou met à jour une playlist dans l'app Musique macOS.

### Usage

```bash
python3 create_playlist.py [OPTIONS]
# ou après pip install :
playlist-create [OPTIONS]
```

### Options

| Option | Défaut | Description |
|--------|--------|-------------|
| `--playlist PATH` | `playlists/orlando_pool_party_2026.json` | Fichier JSON source |
| `--dry-run` | désactivé | Affiche la playlist sans modifier Apple Music |
| `--allow-duplicates` | désactivé | N'ignore pas les morceaux déjà présents |
| `--engine ENGINE` | `applescript` | `applescript` (recommandé) ou `musickit` (expérimental) |
| `--storefront CODE` | `us` | Storefront MusicKit (`us`, `ch`, `fr`…) |
| `--cache PATH` | `cache/musickit_catalog.json` | Cache MusicKit (moteur musickit uniquement) |
| `--no-cache` | désactivé | Désactive le cache MusicKit |

### Exemples

```bash
# Prévisualisation safe
python3 create_playlist.py --dry-run

# Playlist personnalisée
python3 create_playlist.py --playlist playlists/ma_playlist.json

# Autoriser les doublons (mode incrémental)
python3 create_playlist.py --allow-duplicates

# MusicKit — EXPÉRIMENTAL, licence payante requise
export APPLE_MUSIC_DEVELOPER_TOKEN="..."
export APPLE_MUSIC_USER_TOKEN="..."
python3 create_playlist.py --engine musickit --storefront us
```

### Codes de sortie

| Code | Signification |
|------|---------------|
| `0` | Succès |
| `1` | Fichier introuvable ou JSON invalide |
| `2` | Tokens MusicKit manquants |
| `3` | Erreur API MusicKit |
| `4` | Erreurs partielles (certains morceaux en échec) |

### Rapport généré

`reports/report_YYYYMMDD_HHMMSS.txt` — liste des morceaux non trouvés, ignorés et erreurs.

---

## Outil macOS — ouvrir le rapport

```bash
zsh tools/open_report.command
```

Ouvre le rapport HTML catalogue le plus récent.

---

## Variables d'environnement (MusicKit uniquement)

| Variable | Description |
|----------|-------------|
| `APPLE_MUSIC_DEVELOPER_TOKEN` | JWT signé avec clé MusicKit Apple Developer |
| `APPLE_MUSIC_USER_TOKEN` | Token utilisateur bibliothèque Apple Music |

**Non requises** pour le workflow AppleScript standard.

---

## Combinaisons recommandées

### Première création Orlando

```bash
python3 check_catalog.py --country us
open reports/catalog_matches_*.html
# → ajouter les morceaux manquants
python3 create_playlist.py
```

### Mise à jour après modification JSON

```bash
python3 create_playlist.py --dry-run    # vérifier
python3 create_playlist.py              # appliquer
```

### Debug catalogue

```bash
python3 check_catalog.py --no-cache --sleep 1.0
```

---

*En Guidewire, on documente les batch jobs pareil. Sauf que là, le batch c'est « mettre de la bonne vibe ».*
