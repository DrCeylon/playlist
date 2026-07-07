# AGENTS.md

## Cursor Cloud specific instructions

This repo is primarily a **Python 3.12 stdlib-only CLI** (Apple Music Playlist Builder). There are **no servers, databases, or long-running services** — everything is CLI-invoked. See `README.md` (in French) for the full product workflow and command reference.

### Environment / how to run things

- Dependencies are installed into a **`.venv`** created with `python3.12` (see the startup update script). Use `.venv/bin/python ...` (or `source .venv/bin/activate`) for all commands. The `README.md` and `Makefile` use bare `python3`/`python`, which on this VM is not the venv — prefer the venv interpreter.
- **Tests:** `.venv/bin/python -m pytest -q`. The suite makes **live network calls to `itunes.apple.com`** and takes ~2 minutes; a slow run is normal, not a hang.
- `tests/test_app_icon_assets.py` needs **Pillow**, which is *not* declared in `pyproject.toml`/`requirements-dev.txt`. The update script installs it so the full suite (351 tests) collects and passes.
- **No linter** is configured (no ruff/mypy config despite the ignored cache dirs).

### Running the CLI (core product)

The three entry points are `generate_playlist.py`, `check_catalog.py`, and `create_playlist.py` (also installed as `playlist-generate`, `playlist-check-catalog`, `playlist-create`). `generate_playlist.py` and `check_catalog.py` work on Linux (they only need outbound internet to the public iTunes API).

- `create_playlist.py`'s default `applescript` engine **requires macOS + the Music.app** and is guarded by a macOS check, so it cannot actually create playlists on this Linux VM. Use `create_playlist.py --dry-run` to preview the import flow here.
- The `musickit` engine is **experimental** and needs a paid Apple Developer account with `APPLE_MUSIC_DEVELOPER_TOKEN` and `APPLE_MUSIC_USER_TOKEN`. Not needed for the default/recommended workflow.

### Resonance macOS app (`apps/resonance/`)

Secondary SwiftUI **macOS-only** app (Swift Package Manager, macOS 14+). It **cannot be built or tested on this Linux VM** (no Swift toolchain); its CI (`.github/workflows/resonance-macos.yml`) runs only on `macos-latest`.
