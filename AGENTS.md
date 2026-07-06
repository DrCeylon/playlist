# AGENTS.md

À lire avant **chaque** tâche. Court et impératif. Détails dans `docs/engineering/RESONANCE_ENGINEERING_HANDBOOK.md`.

## Vision produit (à ne jamais oublier)

- **Resonance est un moteur universel de playlists**, pas une application Apple Music.
- **Apple Music est un provider** parmi d'autres, pas le centre du système.
- Le produit compose et gère un état de playlist **canonique** ; les providers résolvent, acquièrent et livrent.

## Invariants d'architecture (non négociables)

- Le **Core ne doit jamais dépendre d'un provider** (aucun import de `integration.apple_music`, aucun `persistent_id` / URI Spotify dans les contrats partagés).
- Toute logique **provider-specific reste dans `playlist_builder/integration/<provider>`**.
- Le **bridge runtime** (`playlist_builder/app/bridge_runtime/`) doit rester **provider-neutral** : jamais d'AppleScript ni d'import provider direct.
- Les dépendances pointent **vers l'intérieur** : `canonical/` → ports → application → gateway → providers.

## Règles de travail

- **Small commits** : un commit = un changement logique.
- **Pas de changement UX** sans demande explicite.
- **Pas de Spotify / YouTube Music** sans **ADR** dédié accepté.
- **Toujours lancer les tests disponibles** (`python3.12 -m pytest -q`) avant de conclure.
- **Toujours fournir un rapport final structuré** (fichiers touchés, résumé, validation, état git, prochaine action).
- Ne pas ouvrir de nouvelle phase / gros refactor sans que ce soit demandé.

## Repères

- Phase courante et objectif immédiat : `docs/engineering/CURRENT_PHASE.md`.
- Backlog priorisé : `docs/engineering/NEXT_BACKLOG.md`.
- Checklist de revue : `docs/engineering/REVIEW_CHECKLIST.md`.
- Décisions figées : `docs/engineering/ARCHITECTURE_DECISIONS.md` et `docs/architecture/ADR-*`.

## Cursor Cloud specific instructions

Repo **Python 3.12+** (core stdlib-only, aucune dépendance runtime). Aucun serveur / base de données / service long à lancer.

- Environnement : un virtualenv est provisionné dans `.venv` par le script de mise à jour. Lancer les outils via `.venv/bin/python ...` (ou `source .venv/bin/activate`). `tests/conftest.py` échoue volontairement si Python < 3.12.
- `Pillow` n'est requis que par `tests/test_app_icon_assets.py` ; sans lui la suite échoue à la collecte. Il est installé par le script de mise à jour.
- Tests (suite complète) : `.venv/bin/python -m pytest -q` (~2 min ; ~352 passed, 1 skipped). Aussi `make test`.
- **Aucun linter/formatter n'est configuré** (ni ruff/flake8/black/mypy) : `pytest` est la seule barrière qualité.
- `create_playlist.py` est **macOS-only** (AppleScript) ; sur Linux il sort avec un message « nécessite macOS » — comportement attendu.
- L'app Swift `apps/resonance/` **ne compile pas sur Linux** (pas de toolchain Swift) ; sa logique est couverte par les tests Python du bridge. `scripts/check_all.sh` inclut le build Swift : sur Linux ne lancer que ses deux premières étapes (`scripts/check_environment.py` + `pytest`).
- Découverte catalogue : `generate_playlist.py` / `check_catalog.py` interrogent l'API iTunes **publique** d'Apple (aucun identifiant). `reports/`, `cache/`, `data/`, `.venv/` sont gitignored ; `playlists/` est suivi — ne pas y committer de playlists jetables.
