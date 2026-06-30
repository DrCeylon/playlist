# E2E Apple Music Provider Gateway

This guide validates the full Apple Music flow on macOS with Music.app installed.

## Prerequisites

- macOS with Music.app available
- Python 3.12+
- Repository dependencies installed
- Apple Music account signed in (for catalog acquisition)

## 1. Run unit tests

```bash
git checkout main
git pull
python -m pytest -q
```

All tests must pass before the real E2E run.

## 2. Reset identity cache (optional)

Use a dedicated cache file so the E2E run exercises resolution from scratch:

```bash
rm -f cache/e2e_apple_music_identity.json
```

## 3. Run the gateway import

```bash
python create_playlist.py \
  --playlist playlists/e2e_apple_gateway.json \
  --identity-cache cache/e2e_apple_music_identity.json \
  --json-diagnostics
```

The E2E playlist contains **Kygo — Firestone** only.

## Expected outcomes

| Situation | Result |
|-----------|--------|
| Track already in library | `added` |
| Track only in catalog | Automatic acquisition (`add URL` + duplicate to Library), then `added` |
| Automatic acquisition fails | `not_found` with explicit message (use `--wait-for-acquisition` for manual fallback) |
| Manual mode (`--wait-for-acquisition`) | Music.app opens, CLI waits, user adds track, Enter, retry, then `added` or `not_found` |

## CLI flags

| Flag | Purpose |
|------|---------|
| `--json-diagnostics` | Write detailed JSON report under `reports/` |
| `--identity-cache PATH` | Provider identity mappings (canonical → Apple persistent ID) |
| `--no-acquire` | Skip catalog-to-library acquisition |
| `--wait-for-acquisition` | Opt in to manual confirmation when automatic acquisition fails |
| `--no-wait-for-acquisition` | Explicit non-interactive mode (default) |
| `--incremental` | Add missing tracks only, without reordering |

## Non-destructive guarantees

- Playlists are never deleted
- Library tracks are never deleted
- Sync mode may clear and rebuild the **target playlist only** (existing behaviour)

## Diagnostics

After a run, check:

- `reports/report_*.txt` — human-readable summary
- `reports/import_diagnostics_*.json` — per-track status (`added`, `skipped`, `not_found`, `error`)
- `cache/e2e_apple_music_identity.json` — populated after successful resolutions

## Manual acquisition fallback

If automatic acquisition does not add the track to your library:

```bash
python create_playlist.py \
  --playlist playlists/e2e_apple_gateway.json \
  --identity-cache cache/e2e_apple_music_identity.json \
  --wait-for-acquisition \
  --json-diagnostics
```

When prompted:

1. Click **+** or **Add to Library** in Music.app
2. Confirm the track appears in your library
3. Press **Enter** in the terminal

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `not_found` immediately | Track not in library and acquisition disabled (`--no-acquire`) |
| Low confidence message | Catalog match below threshold; check artist/title spelling |
| AppleScript error | Music.app closed or permissions denied |
| Empty playlist after sync with all `not_found` | Expected since v1.0.6 — playlist is not cleared when zero tracks resolve |
