# Cursor Cloud Agent Setup

Verified instructions for running agents on the Linux Cursor Cloud VM. Short rules: [AGENTS.md](../../AGENTS.md).

## Prerequisites

- Repo access and Cursor Cloud
- Python **3.12+** (VM default)
- No secrets for default workflow (public iTunes API for catalog checks)

## Environment

```bash
pip install -e ".[dev]"
python3.12 scripts/check_environment.py
python3.12 -m pytest -q
```

| Topic | Detail |
|-------|--------|
| Runtime deps | Stdlib only (`pyproject.toml`) |
| Dev deps | `pytest>=8.0` |
| Pillow | Optional — `tests/test_app_icon_assets.py` skips if absent |
| Linter | None configured — **pytest is the quality gate** |
| `pythonpath` | `pyproject.toml` sets `pythonpath = ["."]` for `tests.e2e` imports |

## What works on Linux VM

| Works | Does not work |
|-------|----------------|
| Full Python test suite (~574 pass, 1 skip, ~2 min) | Swift build (`apps/resonance/`) |
| Bridge JSON-RPC contract tests | `create_playlist.py` AppleScript (macOS only) |
| Sync plan/apply with fakes | Music.app import |
| `generate_playlist.py` / `check_catalog.py` (public iTunes API) | `scripts/check_all.sh` Swift step |

On Linux, run only:

```bash
python3.12 scripts/check_environment.py
python3.12 -m pytest -q
```

## Isolation

- `reports/`, `cache/`, `data/`, `.venv/` are gitignored
- Do not commit personal playlists or credentials
- E2E tests use isolated `tmp_path` — see [E2E_TEST_STRATEGY.md](../E2E_TEST_STRATEGY.md)

## Prompt template

```text
Read AGENTS.md and docs/engineering/ENGINEERING_GUIDE.md first.

Task: <specific objective>
Constraints:
- local-first multi-provider; Apple Music is a provider, not the center
- architecture invariants; no UX change unless requested
- python3.12 -m pytest -q before finish
- branch cursor/<name>-ef21 off main

Out of scope: <explicit exclusions>
Done when: ENGINEERING_GUIDE.md Definition of Done met
Report: files, summary, test results, git state, next step
```

## Stop criteria

See [ENGINEERING_GUIDE.md](ENGINEERING_GUIDE.md) — stop when done, blocked, or out-of-scope.

## After the agent returns

1. Verify scope and invariants (`git diff`)
2. Re-run `python3.12 -m pytest -q`
3. Walk [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md) before merge
