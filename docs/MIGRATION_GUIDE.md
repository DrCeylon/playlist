# Migration Guide — vers Resonance v1.0.0

Guide pour utilisateurs et contributeurs passant d'un clone `main` antérieur à juillet 2026 vers la **v1.0.0** taguée.

## Pour les utilisateurs CLI

### Aucun changement de commande requis

Les scripts racine restent identiques :

```bash
python3 check_catalog.py --country us
python3 generate_playlist.py --name "Ma playlist" --seed "Artiste:Titre"
python3 create_playlist.py
```

Les entry points pip (après `pip install -e .`) :

```bash
playlist-check-catalog --country us
playlist-generate --help
playlist-create
```

### Version affichée

Après migration, `diagnostics` bridge et logs peuvent afficher `engine_version: 1.0.0` (auparavant `1.1.0` ou divergent). **Aucun impact fonctionnel.**

### Fichiers locaux

| Chemin | Action |
|--------|--------|
| `data/playlists/managed_playlists.json` | Conservé — format stable Phase 6.3+ |
| `data/history/sessions.json` | Conservé |
| `cache/apple_music_identity.json` | Régénéré si absent |
| `reports/` | Ignoré par git — conserver ou supprimer librement |

Pas de migration de schéma requise pour v1.0.0 si vous êtes déjà sur `main` post-Phase 6.3.

## Pour les utilisateurs app macOS

1. Mettre à jour le dépôt : `git pull origin main` (ou checkout tag `v1.0.0`).
2. Reconstruire :

```bash
cd apps/resonance
./scripts/build.sh
# ou package .app
./scripts/package-mac-app.sh
```

3. Relancer Resonance depuis Xcode ou le `.app` généré.

### Données app

L'app lit le moteur Python du dépôt cloné (bridge subprocess). **Même clone = même données** (`data/` à la racine du repo).

## Pour les contributeurs

### Setup mis à jour

```bash
./scripts/setup_dev.sh
source .venv/bin/activate
python -m pytest -q
```

### Nouveaux fichiers attendus

| Fichier | Rôle |
|---------|------|
| `LICENSE` | MIT |
| `SECURITY.md` | Signalement vulnérabilités |
| `CONTRIBUTING.md` | Process contribution |
| `AGENTS.md` | Instructions agents IA |
| `.github/workflows/python-ci.yml` | CI pytest Linux |

### CI locale avant PR

```bash
python -m pytest -q                    # minimum
./scripts/check_all.sh                 # macOS complet
```

### Version unique

Ne pas modifier `pyproject.toml` et `__init__.py` indépendamment — les deux doivent rester sur **1.0.0** jusqu'à la prochaine release.

## Changements de contrat bridge (depuis Phase 4)

Si vous maintenez un fork ancien (pré-4.6) :

| Ancien | v1.0 |
|--------|------|
| Pas de bridge runtime | Commands JSON-RPC standard (`generate`, `import_stream`, `plan_sync`, `apply_sync`, …) |
| Pas de repository local | `ManagedPlaylistRepository` obligatoire pour sync |
| Import monolithique | `import_stream` avec checkpoints |

Référence DTO : `playlist_builder/ui/shared/dto/` ↔ `ResonanceCore`.

## Depuis versions « 0.8.x » packaging

`pyproject.toml` passait de `0.8.2` à `1.0.0` — reflet sémantique produit, pas de rupture API Python publique (pas de PyPI publish automatique).

## Rollback

```bash
git checkout <sha-avant-v1.0.0>
pip install -e ".[dev]"
python -m pytest -q
```

Les fichiers `data/` restent compatibles en général ; tester sync operations si rollback après apply 6.5.

## Support

- Limitations : [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)
- Compatibilité : [COMPATIBILITY_MATRIX.md](COMPATIBILITY_MATRIX.md)
- Issues : https://github.com/DrCeylon/playlist/issues
