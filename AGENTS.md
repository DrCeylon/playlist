# AGENTS.md

## Cursor Cloud specific instructions

This repo is a **Python 3.12+ multi-product monorepo** (no external runtime deps; the core CLI is stdlib-only). There is no server, database, or long-running service to start.

### Products / what can run on Linux (the cloud VM)
- **Python core + CLI (`playlist_builder/`, `generate_playlist.py`, `check_catalog.py`, `create_playlist.py`)** — the primary product. Fully developed/tested on Linux.
  - `create_playlist.py` is **macOS-only** (drives Apple Music via AppleScript); on Linux it intentionally exits with a "nécessite macOS" message. This is expected, not a bug.
- **Shared UI logic + JSON-RPC engine bridge (`playlist_builder/ui/`, `playlist_builder.cli.engine_bridge`)** — pure Python; the macOS app drives it as a subprocess. Fully testable on Linux via pytest.
- **Swift/macOS app `apps/resonance/`** — **cannot build on Linux** (no Swift toolchain; `apps/resonance/scripts/build.sh` aborts with "Swift toolchain not found"). Its logic is covered by the Python bridge tests. `scripts/check_all.sh` includes this Swift build step, so on Linux only run its first two steps (`scripts/check_environment.py` + `pytest`).

### Environment
- A virtualenv is created at `.venv` (the update script provisions it). Run tools via `.venv/bin/python ...` or `source .venv/bin/activate` first.
- `tests/conftest.py` hard-fails if Python < 3.12. The default `python3` here is 3.12.
- `Pillow` is required by `tests/test_app_icon_assets.py` only; without it the full suite errors at collection. It is installed by the update script.

### Common commands (run from repo root)
- Test (full suite): `.venv/bin/python -m pytest -q` (~2 min; expect ~352 passed, 1 skipped). Also `make test`.
- Env check: `.venv/bin/python scripts/check_environment.py`
- Generate a playlist (hits Apple's **public** iTunes catalog API over the internet; no credentials): `.venv/bin/python generate_playlist.py --name "X" --seed "Kygo:Firestone" --keywords "tropical,dance" --duration 60 --country us --output playlists/x.json`. Use `--no-catalog` to skip network.
- Verify a playlist against the catalog: `.venv/bin/python check_catalog.py --playlist playlists/x.json --country us` → writes `reports/*.csv` and `reports/*.html`.

### Notes
- **No linter/formatter is configured** anywhere (no ruff/flake8/black/mypy). The only quality gate is `pytest`.
- `reports/`, `cache/`, `data/`, and `.venv/` are gitignored; `playlists/` is tracked — don't commit throwaway generated playlists there.
